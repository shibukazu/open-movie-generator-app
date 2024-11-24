import io
import logging
import os
import wave
from ctypes import CDLL
from pathlib import Path
from typing import List, Literal, TypedDict

from .audio_generator import Audio, Detail, IAudioGenerator, Manuscript


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
        logger: logging.Logger,
        output_dir: str,
        onnxruntime_lib_path: str,
        open_jtalk_dict_dir_path: str,
        content_speaker_id: int | None = None,
    ):
        super().__init__(logger, output_dir)
        self.content_speaker_id = content_speaker_id
        self.onnxruntime_lib_path = onnxruntime_lib_path
        self.open_jtalk_dict_dir_path = open_jtalk_dict_dir_path

    def generate(self, manuscript: Manuscript) -> Audio:
        CDLL(
            str(
                Path(
                    self.onnxruntime_lib_path,
                ).resolve(strict=True)
            )
        )

        from voicevox_core import VoicevoxCore  # type: ignore  # noqa: E402

        vv_core = VoicevoxCore(open_jtalk_dict_dir=Path(self.open_jtalk_dict_dir_path))

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

        # コンテンツの音声を生成
        content_details: list[Detail] = []
        for idx, content in enumerate(manuscript.contents):
            try:
                content_output_audio_file_path = os.path.join(
                    self.output_dir, "audio", f"{idx}.wav"
                )
                os.makedirs(
                    os.path.dirname(content_output_audio_file_path), exist_ok=True
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

            audio = Audio(content_details=content_details)

        self.logger.info("VOICEVOXを用いた動画音声を生成しました")

        return audio
