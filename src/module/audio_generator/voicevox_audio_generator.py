import io
import json
import logging
import os
import wave
from ctypes import CDLL
from pathlib import Path

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

with open(
    Path(current_dir, "../../resource/common/voicevox_speaker_attributes.json"), "r"
) as f:
    speaker_attributes = json.load(f)["speaker_attributes"]


class VoiceVoxAudioGenerator(IAudioGenerator):
    def __init__(self, id: str, logger: logging.Logger):
        super().__init__(id, logger)
        self.output_dir = os.path.join(current_dir, "../../../output", self.id, "audio")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, manuscript: Manuscript) -> Audio:
        unique_user_ids = list(
            set([content.speaker_id for content in manuscript.contents])
        )
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
                raise Exception(f"Failed to generate audio for comment: {content.text}")

            audio = Audio(
                overview_detail=overview_detail, content_details=content_details
            )

            dump = audio.model_dump_json()

            with open(self.dump_file_path, "w") as f:
                f.write(dump)
        self.logger.info("VoiceVox audio genaration success")

        return audio
