import io
import logging
import os
import wave
from ctypes import CDLL
from pathlib import Path
from typing import List, Literal, TypedDict

from dotenv import load_dotenv

from .audio_generator import Audio, Detail, IAudioGenerator, Manuscript

load_dotenv()
ONNXRUNTIME_LIB_PATH = os.getenv("ONNXRUNTIME_LIB_PATH")
if not ONNXRUNTIME_LIB_PATH:
    raise ValueError("ONNXRUNTIME_LIB_PATH is not set")
OPEN_JTALK_DICT_DIR_PATH = os.getenv("OPEN_JTALK_DICT_DIR_PATH")
if not OPEN_JTALK_DICT_DIR_PATH:
    raise ValueError("OPEN_JTALK_DICT_DIR_PATH is not set")


current_dir = os.path.dirname(os.path.abspath(__file__))

CDLL(
    str(
        Path(
            current_dir,
            ONNXRUNTIME_LIB_PATH,
        ).resolve(strict=True)
    )
)

from voicevox_core import VoicevoxCore  # type: ignore  # noqa: E402

vv_core = VoicevoxCore(open_jtalk_dict_dir=Path(current_dir, OPEN_JTALK_DICT_DIR_PATH))


class SpeakerAttribute(TypedDict):
    value: int
    label: str
    gender: Literal["woman", "man"]


speaker_attributes: List[SpeakerAttribute] = [
    {"value": 3, "label": "ずんだもん", "gender": "woman"},
    {"value": 2, "label": "四国めたん", "gender": "woman"},
    {"value": 9, "label": "波音リツ", "gender": "woman"},
    {"value": 14, "label": "冥鳴ひまり", "gender": "woman"},
    {"value": 13, "label": "青山龍星", "gender": "man"},
    {"value": 52, "label": "雀松朱司", "gender": "man"},
    {"value": 51, "label": "聖騎士 紅桜", "gender": "man"},
]


class VoiceVoxAudioGenerator(IAudioGenerator):
    def __init__(
        self,
        id: str,
        logger: logging.Logger,
        overview_speaker_id: int | None = None,
        content_speaker_id: int | None = None,
        ending_speaker_id: int | None = None,
    ):
        super().__init__(id, logger)
        self.overview_speaker_id = overview_speaker_id
        self.content_speaker_id = content_speaker_id
        self.ending_speaker_id = ending_speaker_id
        self.output_dir = os.path.join(current_dir, "../../../output", self.id, "audio")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, manuscript: Manuscript) -> Audio:
        if self.overview_speaker_id is not None:
            overview_speaker_id = self.overview_speaker_id
        else:
            overview_speaker_id = 3  # 個人的な好みでずんだもんを選択

        unique_user_ids = list(
            set([content.speaker_id for content in manuscript.contents])
        )
        if self.content_speaker_id is not None:
            # 指定された場合はすべての内容を同一話者で話す
            content_speaker_attribute = None
            for speaker_attribute in speaker_attributes:
                if speaker_attribute["value"] == self.content_speaker_id:
                    content_speaker_attribute = speaker_attribute
                    break
            if content_speaker_attribute is None:
                raise ValueError(
                    f"次の話者IDはサポートされていません: {self.content_speaker_id}"
                )
            unique_user_id_to_speaker_attribute = {
                user_id: content_speaker_attribute
                for i, user_id in enumerate(unique_user_ids)
            }

        else:
            unique_user_id_to_speaker_attribute = {
                user_id: speaker_attributes[i % len(speaker_attributes)]
                for i, user_id in enumerate(unique_user_ids)
            }

        # Overviewの音声を生成
        overview_output_audio_file_path = os.path.join(self.output_dir, "overview.wav")
        os.remove(overview_output_audio_file_path) if os.path.exists(
            overview_output_audio_file_path
        ) else None

        overview_speaker_id = 3  # ずんだもん
        vv_core.load_model(overview_speaker_id)
        overview_audio_query = vv_core.audio_query(
            manuscript.overview, speaker_id=overview_speaker_id
        )
        overview_wav = vv_core.synthesis(overview_audio_query, overview_speaker_id)
        with wave.open(overview_output_audio_file_path, "wb") as overview_output_wav:
            with wave.open(io.BytesIO(overview_wav), "rb") as wav:
                overview_output_wav.setnchannels(wav.getnchannels())
                overview_output_wav.setsampwidth(wav.getsampwidth())
                overview_output_wav.setframerate(wav.getframerate())
                overview_output_wav.writeframes(wav.readframes(wav.getnframes()))
        overview_detail = Detail(
            wav_file_path=overview_output_audio_file_path,
            transcript=manuscript.overview,
            speaker_id=str(overview_speaker_id),
            speaker_gender="woman",
            tags=[],
        )

        # コンテンツの音声を生成
        content_details: list[Detail] = []
        for idx, content in enumerate(manuscript.contents):
            try:
                content_output_audio_file_path = os.path.join(
                    self.output_dir, f"{idx}.wav"
                )
                os.remove(content_output_audio_file_path) if os.path.exists(
                    content_output_audio_file_path
                ) else None
                content_speaker_id = unique_user_id_to_speaker_attribute[
                    content.speaker_id
                ]["value"]
                content_speaker_gender = unique_user_id_to_speaker_attribute[
                    content.speaker_id
                ]["gender"]
                vv_core.load_model(content_speaker_id)
                content_audio_query = vv_core.audio_query(
                    content.text, speaker_id=content_speaker_id
                )
                content_wav = vv_core.synthesis(content_audio_query, content_speaker_id)
                with wave.open(
                    content_output_audio_file_path, "wb"
                ) as content_output_wav:
                    with wave.open(io.BytesIO(content_wav), "rb") as wav:
                        content_output_wav.setnchannels(wav.getnchannels())
                        content_output_wav.setsampwidth(wav.getsampwidth())
                        content_output_wav.setframerate(wav.getframerate())
                        content_output_wav.writeframes(wav.readframes(wav.getnframes()))

                        content_details.append(
                            Detail(
                                wav_file_path=content_output_audio_file_path,
                                transcript=content.text,
                                speaker_id=str(content_speaker_id),
                                speaker_gender=content_speaker_gender,
                                tags=[],
                            )
                        )
            except Exception:
                raise Exception(
                    f"次のコンテンツの音声生成に失敗しました: {content.text}"
                )

            audio = Audio(
                overview_detail=overview_detail, content_details=content_details
            )

            dump = audio.model_dump_json()

            with open(self.dump_file_path, "w") as f:
                f.write(dump)

        self.logger.info("VOICEVOXを用いた動画音声を生成しました")

        return audio
