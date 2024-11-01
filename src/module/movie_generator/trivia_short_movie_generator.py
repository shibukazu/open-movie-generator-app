import logging
import os
import random
import sys
import wave
from typing import List

from dotenv import load_dotenv
from moviepy.audio.fx.all import audio_loop, volumex
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
)
from openai import OpenAI

from ..audio_generator import Audio
from ..manuscript_generator import Manuscript
from .movie_generator import IMovieGenerator

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import ImageGenerator, tokenize  # noqa: E402

load_dotenv()

FONT_PATH = os.getenv("FONT_PATH")

current_dir = os.path.dirname(os.path.abspath(__file__))

bgm_dir = os.path.join(current_dir, "../../../material/movie/bgm")
bgm_file_list = [
    os.path.join(bgm_dir, f)
    for f in os.listdir(bgm_dir)
    if os.path.isfile(os.path.join(bgm_dir, f)) and f != ".gitkeep"
]
if len(bgm_file_list) == 0:
    raise FileNotFoundError(f"次のディレクトリ内にBGMが見つかりません: {bgm_dir}")
bgm_file_path = bgm_file_list[random.randint(0, len(bgm_file_list) - 1)]


class TriviaShortMovieGenerator(IMovieGenerator):
    def __init__(self, id: str, openai_apikey: str, logger: logging.Logger):
        super().__init__(id, logger)
        self.openai_client = OpenAI(api_key=openai_apikey)
        self.output_movie_path = os.path.join(
            current_dir, "../../../output", self.id, "movie.mp4"
        )
        self.image_generator = ImageGenerator(
            openai_apikey=openai_apikey, logger=logger
        )
        os.makedirs(os.path.dirname(self.output_movie_path), exist_ok=True)

    def generate(self, manuscript: Manuscript, audio: Audio) -> None:
        # 音声を順次結合し、それに合わせて動画を作成する
        video_clips = []
        audio_clips: List[AudioFileClip] = []
        start_time = 0.0
        total_duration = 0.0

        # trivia では最初にサムネイル画像を3s表示する
        thumbnail_image_path = os.path.join(
            current_dir, "../../../output/", self.id, "thumbnail_original.png"
        )
        intro_duration = 3.0
        image_clip = (
            ImageClip(thumbnail_image_path)
            .resize(height=1920)
            .set_start(start_time)
            .set_duration(intro_duration)
        )

        video_clip = [image_clip]
        video_clips += video_clip
        start_time += intro_duration
        total_duration += intro_duration

        # 次にcontentsを紹介する
        for idx, content_detail in enumerate(audio.content_details):
            content_transcript = content_detail.transcript
            content_wav_file_path = content_detail.wav_file_path
            with wave.open(content_wav_file_path, "rb") as wav:
                audio_duration = round(wav.getnframes() / wav.getframerate(), 2)
                # Shortsの制約に基づき60s以内の動画を生成する
                if start_time + audio_duration > 60:
                    break
                # 内容にふさわしい画像を生成する
                background_image_path = os.path.join(
                    current_dir, "../../../output/", self.id, "movie", f"{idx}.png"
                )
                self.image_generator.generate_from_text(
                    text=content_transcript,
                    image_path=background_image_path,
                    image_size="1024x1024",
                )
                font_size = 50
                num_text_per_line = 1080 // font_size
                wrapped_texts = []
                line = ""
                for token in tokenize(content_detail.transcript):
                    if len(line) + len(token) >= num_text_per_line:
                        wrapped_texts.append(line)
                        line = ""
                    line += token
                if line:
                    wrapped_texts.append(line)

                audio_clip = (
                    AudioFileClip(content_wav_file_path)
                    .set_start(start_time)
                    .set_duration(audio_duration)
                    .fx(volumex, 1.0)
                )
                subtitle_clips = []
                if len(wrapped_texts) == 1:
                    subtitle_clip = (
                        TextClip(
                            content_transcript,
                            font=FONT_PATH,
                            fontsize=50,
                            color="black",
                        )
                        .set_position(("center", 1500))
                        .set_start(start_time)
                        .set_duration(audio_duration)
                    )
                    subtitle_clips.append(subtitle_clip)
                else:
                    line_height = 70
                    for i, subtext in enumerate(wrapped_texts):
                        subtitle_clip = (
                            TextClip(
                                subtext,
                                font=FONT_PATH,
                                fontsize=50,
                                color="black",
                            )
                            .set_start(start_time)
                            .set_duration(audio_duration)
                            .set_position(("center", 1400 + line_height * i))
                        )
                        subtitle_clips.append(subtitle_clip)

                white_background_clip = (
                    ColorClip(size=(1080, 1920), color=(255, 255, 255))
                    .set_start(start_time)
                    .set_duration(audio_duration)
                )
                image_clip = (
                    ImageClip(background_image_path)
                    .set_position(("center", "center"))
                    .set_start(start_time)
                    .set_duration(audio_duration)
                )

                video_clip = [white_background_clip, image_clip] + subtitle_clips
                video_clips += video_clip
                audio_clips.append(audio_clip)
                start_time += audio_duration
                total_duration += audio_duration

        # BGM
        bgm_clip = (
            AudioFileClip(bgm_file_path)
            .fx(audio_loop, duration=total_duration)
            .fx(volumex, 0.1)
        )

        # クリップの合成
        video = CompositeVideoClip(video_clips)
        audio = CompositeAudioClip([bgm_clip] + audio_clips)
        video = video.set_audio(audio)

        # 動画の保存
        os.remove(self.output_movie_path) if os.path.exists(
            self.output_movie_path
        ) else None
        video.write_videofile(
            self.output_movie_path,
            codec="libx264",
            fps=30,
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
        )

        self.logger.info("Trivia short movie generation success")

        self.upload_manager.register(self.id)

        return
