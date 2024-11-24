import logging
import os
import sys
import wave
from typing import List

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

from util import ImageGenerator, wrap_text  # noqa: E402


class DalleShortMovieGenerator(IMovieGenerator):
    def __init__(
        self,
        openai_apikey: str,
        logger: logging.Logger,
        bgm_file_path: str,
        font_path: str,
        output_dir: str,
    ):
        super().__init__(
            is_short=False,
            logger=logger,
            font_path=font_path,
            output_dir=output_dir,
        )
        self.openai_client = OpenAI(api_key=openai_apikey)
        self.image_generator = ImageGenerator(
            openai_apikey=openai_apikey, logger=logger
        )
        self.bgm_file_path = bgm_file_path

    def generate(self, manuscript: Manuscript, audio: Audio) -> None:
        width, height = 1080, 1920
        font_size = 50

        # 音声を順次結合し、それに合わせて動画を作成する
        video_clips = []
        audio_clips: List[AudioFileClip] = []
        start_time = 0.0
        total_duration = 0.0

        # trivia では最初にサムネイル画像を3s表示する
        thumbnail_image_path = os.path.join(self.output_dir, "thumbnail_original.png")
        intro_duration = 3.0
        image_clip = (
            ImageClip(thumbnail_image_path)
            .resize(height=height)
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
                if start_time + audio_duration >= 60:
                    break
                # 内容にふさわしい画像を生成する
                background_image_path = os.path.join(
                    self.output_dir, "movie", f"{idx}.png"
                )
                self.image_generator.generate_from_text(
                    text=content_transcript,
                    image_path=background_image_path,
                    image_size="1024x1024",
                )
                wrapped_texts = wrap_text(content_transcript, width // font_size)

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
                            font=self.font_path,
                            fontsize=font_size,
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
                                font=self.font_path,
                                fontsize=font_size,
                                color="black",
                            )
                            .set_start(start_time)
                            .set_duration(audio_duration)
                            .set_position(("center", 1500 + line_height * i))
                        )
                        subtitle_clips.append(subtitle_clip)

                white_background_clip = (
                    ColorClip(size=(width, height), color=(255, 255, 255))
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
            AudioFileClip(self.bgm_file_path)
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

        self.logger.info(
            f"Dall-Eを用いた短尺動画を生成しました: {self.output_movie_path}"
        )

        return
