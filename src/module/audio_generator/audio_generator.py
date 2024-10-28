import abc
import logging
import os
from typing import List, Literal

from pydantic import BaseModel, Field

from ..manuscript_generator import Manuscript

current_dir = os.path.dirname(os.path.abspath(__file__))


class Detail(BaseModel):
    wav_file_path: str = Field(description="音声ファイルのパス")
    transcript: str = Field(description="音声のテキスト")
    speaker_id: str = Field(description="話者ID")
    speaker_gender: Literal["woman", "man"] = Field(description="話者の性別")
    tags: List[str] = Field(description="タグ")


class Audio(BaseModel):
    overview_detail: Detail = Field(description="概要の音声詳細")
    content_details: List[Detail] = Field(description="音声の詳細")


class IAudioGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        self.id = id
        self.logger = logger
        self.dump_file_path = os.path.join(
            current_dir, "../../../output", self.id, "audio.json"
        )
        self.audio_file_path = os.path.join(
            current_dir, "../../../output", self.id, "audio.wav"
        )
        os.makedirs(os.path.dirname(self.dump_file_path), exist_ok=True)

    def skip(self) -> Audio:
        if not os.path.exists(self.dump_file_path):
            raise FileNotFoundError(f"Audio dump file not found: {self.dump_file_path}")
        with open(self.dump_file_path, "r") as f:
            dump = f.read()
        audio = Audio.model_validate_json(dump)
        return audio

    @abc.abstractmethod
    def generate(self, manuscript: Manuscript) -> Audio:
        pass
