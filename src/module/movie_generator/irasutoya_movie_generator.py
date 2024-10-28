import logging
import os
import random
import wave

from dotenv import load_dotenv
from moviepy.audio.fx.all import audio_loop, volumex
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
)

from ..audio_generator import Audio
from ..manuscript_generator import Manuscript
from .movie_generator import IMovieGenerator

load_dotenv()

FONT_PATH = os.getenv("FONT_PATH")

current_dir = os.path.dirname(os.path.abspath(__file__))

image_dir = os.path.join(current_dir, "../../../material/image/irasutoya")
image_file_list = [
    os.path.join(image_dir, f)
    for f in os.listdir(image_dir)
    if os.path.isfile(os.path.join(image_dir, f))
]
bgm_dir = os.path.join(current_dir, "../../../material/bgm")
bgm_file_list = [
    os.path.join(bgm_dir, f)
    for f in os.listdir(bgm_dir)
    if os.path.isfile(os.path.join(bgm_dir, f))
]
bgm_file_path = bgm_file_list[random.randint(0, len(bgm_file_list) - 1)]
bgv_dir = os.path.join(current_dir, "../../../material/bgv")
bgv_file_list = [
    os.path.join(bgv_dir, f)
    for f in os.listdir(bgv_dir)
    if os.path.isfile(os.path.join(bgv_dir, f))
]
bgv_file_path = bgv_file_list[random.randint(0, len(bgv_file_list) - 1)]

woman_speaker_image_file_list = [
    image_file for image_file in image_file_list if "_woman_" in image_file
]
man_speaker_image_file_list = [
    image_file for image_file in image_file_list if "_man_" in image_file
]


class IrasutoyaMovieGenerator(IMovieGenerator):
    def __init__(self, id: str, logger: logging.Logger):
        super().__init__(id, logger)
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
        # irasutoya_movie_generatorでは始めにoverviewを紹介する
        overview_detail = audio.overview_detail
        overview_wav_file_path = overview_detail.wav_file_path
        with wave.open(overview_wav_file_path, "rb") as wav:
            audio_duration = round(wav.getnframes() / wav.getframerate(), 2)
            audio_clip = (
                AudioFileClip(overview_wav_file_path)
                .set_start(start_time)
                .set_duration(audio_duration)
                .fx(volumex, 1.0)
            )
            subtitle_clip = (
                TextClip(
                    manuscript.title,
                    font=FONT_PATH,
                    fontsize=50,
                    color="black",
                )
                .set_position(("center", 800))
                .set_start(start_time)
                .set_duration(audio_duration)
            )
            video_clip = [subtitle_clip]
            video_clips += video_clip
            audio_clips.append(audio_clip)
            start_time += audio_duration
            total_duration += audio_duration

        # 次にcontentsを紹介する
        prev_speaker_image_path = None
        prev_speaker_id = None
        for content_detail in audio.content_details:
            content_transcript = content_detail.transcript
            content_wav_file_path = content_detail.wav_file_path
            # 画像の設定
            if content_detail.speaker_id == prev_speaker_id:
                speaker_image_path = prev_speaker_image_path
            else:
                if content_detail.speaker_gender == "man":
                    speaker_image_path = random.choice(man_speaker_image_file_list)
                    while speaker_image_path == prev_speaker_image_path:
                        speaker_image_path = random.choice(man_speaker_image_file_list)
                else:
                    speaker_image_path = random.choice(woman_speaker_image_file_list)
                    while speaker_image_path == prev_speaker_image_path:
                        speaker_image_path = random.choice(
                            woman_speaker_image_file_list
                        )
            # 25文字以上の場合は分割
            # TODO: 日本語の場合は文字数で分割すると意味が変わることがあるので、形態素解析を使って分割する
            splitted_texts = []
            if len(content_detail.transcript) > 25:
                splitted_texts = [
                    content_detail.transcript[i : i + 25]
                    for i in range(0, len(content_detail.transcript), 25)
                ]
            else:
                splitted_texts = [content_detail.transcript]
            prev_speaker_image_path = speaker_image_path
            prev_speaker_id = content_detail.speaker_id
            with wave.open(content_wav_file_path, "rb") as wav:
                audio_duration = round(wav.getnframes() / wav.getframerate(), 2)
                audio_clip = (
                    AudioFileClip(content_wav_file_path)
                    .set_start(start_time)
                    .set_duration(audio_duration)
                    .fx(volumex, 1.0)
                )
                subtitle_clips = []
                if len(splitted_texts) == 1:
                    subtitle_clip = (
                        TextClip(
                            content_transcript,
                            font=FONT_PATH,
                            fontsize=50,
                            color="black",
                        )
                        .set_position(("center", 800))
                        .set_start(start_time)
                        .set_duration(audio_duration)
                    )
                    subtitle_clips.append(subtitle_clip)
                else:
                    line_height = 70
                    for i, subtext in enumerate(splitted_texts):
                        subtitle_clip = (
                            TextClip(
                                subtext,
                                font=FONT_PATH,
                                fontsize=50,
                                color="black",
                            )
                            .set_start(start_time)
                            .set_duration(audio_duration)
                            .set_position(("center", 700 + line_height * i))
                        )
                        subtitle_clips.append(subtitle_clip)
                white_board_edge_clip = (
                    ColorClip(size=(1840, 450), color=(222, 184, 135))
                    .set_position(("center", "bottom"))
                    .set_start(start_time)
                    .set_duration(audio_duration)
                )
                white_board_clip = (
                    ColorClip(size=(1800, 430), color=(255, 255, 255))
                    .set_position(("center", "bottom"))
                    .set_start(start_time)
                    .set_duration(audio_duration)
                )
                image_clip = (
                    ImageClip(speaker_image_path)
                    .resize(height=500)
                    .set_position(("center", 200))
                    .set_start(start_time)
                    .set_duration(audio_duration)
                )

                video_clip = (
                    [white_board_edge_clip, white_board_clip]
                    + subtitle_clips
                    + [image_clip]
                )
                video_clips += video_clip
                audio_clips.append(audio_clip)
                start_time += audio_duration
                total_duration += audio_duration

        # BGV
        bgv_clip = (
            VideoFileClip(bgv_file_path)
            .resize((1920, 1080))
            .loop(duration=total_duration)
        )
        # BGM
        bgm_clip = (
            AudioFileClip(bgm_file_path)
            .fx(audio_loop, duration=total_duration)
            .fx(volumex, 0.1)
        )

        # クリップの合成
        video = CompositeVideoClip([bgv_clip] + video_clips)
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

        self.logger.info("Irasutoya movie generation success")

        return