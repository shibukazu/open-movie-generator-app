import logging
import math
import os
import random
import sys
import wave

os.environ["IMAGEIO_FFMPEG_EXE"] = "/ffmpeg"
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

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import wrap_text  # noqa: E402


class IrasutoyaShortMovieGenerator(IMovieGenerator):
    def __init__(
        self,
        logger: logging.Logger,
        font_path: str,
        output_dir: str,
        man_image_dir: str,
        woman_image_dir: str,
        bgm_file_path: str,
        bgv_file_path: str,
    ):
        super().__init__(
            is_short=False,
            logger=logger,
            font_path=font_path,
            output_dir=output_dir,
        )
        self.man_image_file_paths = [
            os.path.join(man_image_dir, f)
            for f in os.listdir(man_image_dir)
            if os.path.isfile(os.path.join(man_image_dir, f))
        ]
        self.woman_image_file_paths = [
            os.path.join(woman_image_dir, f)
            for f in os.listdir(woman_image_dir)
            if os.path.isfile(os.path.join(woman_image_dir, f))
        ]
        self.bgm_file_path = bgm_file_path
        self.bgv_file_path = bgv_file_path

    def get_random_woman_image_file_path(self) -> str:
        return random.choice(self.woman_image_file_paths)

    def get_random_man_image_file_path(self) -> str:
        return random.choice(self.man_image_file_paths)

    def generate(self, manuscript: Manuscript, audio: Audio) -> None:
        width, height = 1080, 1920
        font_size = 50

        # 音声を順次結合し、それに合わせて動画を作成する
        video_clips = []
        audio_clips = []
        start_time = 0.0
        total_duration = 0.0
        # irasutoya_movie_generatorでは始めにoverviewを紹介する
        thumbnail_image_path = os.path.join(self.output_dir, "thumbnail_original.png")
        overview_duration = 3.0
        image_clip = (
            ImageClip(thumbnail_image_path)
            .resize(height=height)
            .set_start(start_time)
            .set_duration(overview_duration)
        )

        video_clip = [image_clip]
        video_clips += video_clip
        start_time += overview_duration
        total_duration += overview_duration

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
                    speaker_image_path = self.get_random_man_image_file_path()
                    while speaker_image_path == prev_speaker_image_path:
                        speaker_image_path = self.get_random_man_image_file_path()
                else:
                    speaker_image_path = self.get_random_woman_image_file_path()
                    while speaker_image_path == prev_speaker_image_path:
                        speaker_image_path = self.get_random_woman_image_file_path()
            wrapped_texts = wrap_text(content_detail.transcript, width // font_size - 2)

            prev_speaker_image_path = speaker_image_path
            prev_speaker_id = content_detail.speaker_id
            with wave.open(content_wav_file_path, "rb") as wav:
                audio_duration = round(wav.getnframes() / wav.getframerate(), 2)
                # Shortsの制約に基づき60s以内の動画を生成する
                if start_time + audio_duration >= 60:
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
                    for i, text in enumerate(wrapped_texts):
                        subtitle_clip = (
                            TextClip(
                                text,
                                font=self.font_path,
                                fontsize=font_size,
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
                    ImageClip(speaker_image_path)
                    .set_position(
                        lambda t: ("center", 300 + 50 * math.sin(2 * math.pi * t))
                    )
                    .resize(height=900)
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
            VideoFileClip(self.bgv_file_path)
            .resize((width, height))
            .loop(duration=total_duration)
        )
        # BGM
        bgm_clip = (
            AudioFileClip(self.bgm_file_path)
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

        self.logger.info(
            f"いらすとやを用いた短尺動画を生成しました: {self.output_movie_path}"
        )

        return
