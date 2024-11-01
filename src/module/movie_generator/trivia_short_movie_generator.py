import logging
import os
import random
import sys
import wave
from typing import List

import requests
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
from pydantic import BaseModel

from ..audio_generator import Audio
from ..manuscript_generator import Manuscript
from .movie_generator import IMovieGenerator

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import tokenize  # noqa: E402

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


class Keywords(BaseModel):
    keywords: List[str]


class TriviaShortMovieGenerator(IMovieGenerator):
    def __init__(self, id: str, openai_apikey: str, logger: logging.Logger):
        super().__init__(id, logger)
        self.openai_client = OpenAI(api_key=openai_apikey)
        self.output_movie_path = os.path.join(
            current_dir, "../../../output", self.id, "movie.mp4"
        )
        os.makedirs(os.path.dirname(self.output_movie_path), exist_ok=True)

    def generate(self, manuscript: Manuscript, audio: Audio) -> None:
        # 音声を順次結合し、それに合わせて動画を作成する
        video_clips = []
        audio_clips = []
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
            # 内容をふさわしい画像を生成する
            # transcriptのキーワードは一部がOpenAIのSafety Policyに抵触する可能性があるため、一度厳選する
            filter_response = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "system",
                        "content": "ある文章が与えられます。このうち、DALL-Eを用いて文章を十分に表現するような画像を生成するにあたって有用かつDALL-Eの制約に抵触しないキーワードを抽出してください。例えば個人名や不適切な単語が抵触するキーワードです。",
                    },
                    {
                        "role": "user",
                        "content": f"{','.join(manuscript.keywords)}",
                    },
                ],
                response_format=Keywords,
            )

            keywords = filter_response.choices[0].message.parsed
            if not keywords:
                raise ValueError(
                    "動画の背景画像生成に用いるキーワードの抽出に失敗しました。"
                )

            image_generation_response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=f"{','.join(keywords.keywords)}",
                size="1024x1792",
                quality="standard",
                n=1,
            )
            background_image_url = image_generation_response.data[0].url
            if background_image_url is None:
                raise ValueError("DALL-Eでの動画背景画像生成に失敗しました。")
            background_image_path = os.path.join(
                current_dir, "../../../output/", self.id, "movie", f"{idx}.png"
            )
            os.makedirs(os.path.dirname(background_image_path), exist_ok=True)
            os.remove(background_image_path) if os.path.exists(
                background_image_path
            ) else None
            response = requests.get(url=background_image_url)
            if response.status_code == 200:
                with open(background_image_path, "wb") as file:
                    for chunk in response.iter_content(1024):  # 1KBごとに書き込み
                        file.write(chunk)
                self.logger.info(
                    f"動画背景画像をダウンロードしました: {background_image_path}"
                )
            else:
                raise ValueError(
                    f"動画背景画像のダウンロードに失敗しました: {background_image_url}"
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

            with wave.open(content_wav_file_path, "rb") as wav:
                audio_duration = round(wav.getnframes() / wav.getframerate(), 2)
                # Shortsの制約に基づき60s以内の動画を生成する
                if start_time + audio_duration > 60:
                    break
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
                white_board_edge_clip = (
                    ColorClip(size=(1000, 550), color=(222, 184, 135))
                    .set_position(("center", 1300))
                    .set_start(start_time)
                    .set_duration(audio_duration)
                )
                white_board_clip = (
                    ColorClip(size=(960, 530), color=(255, 255, 255))
                    .set_position(("center", 1300))
                    .set_start(start_time)
                    .set_duration(audio_duration)
                )
                image_clip = (
                    ImageClip(background_image_path)
                    .set_start(start_time)
                    .set_duration(audio_duration)
                )

                video_clip = (
                    [image_clip]
                    + [white_board_edge_clip, white_board_clip]
                    + subtitle_clips
                )
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
