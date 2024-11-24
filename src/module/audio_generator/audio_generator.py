import abc
import logging
import os
from typing import List, Literal

from pydantic import BaseModel, Field

from ..manuscript_generator import Manuscript


class Detail(BaseModel):
    wav_file_path: str = Field(description="音声ファイルのパス")
    transcript: str = Field(description="音声のテキスト")
    speaker_id: str = Field(description="話者ID")
    speaker_gender: Literal["woman", "man"] = Field(description="話者の性別")
    tags: List[str] = Field(description="タグ")


class Audio(BaseModel):
    content_details: List[Detail] = Field(description="音声の詳細")


class IAudioGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, logger: logging.Logger, output_dir: str) -> None:
        self.id = id
        self.logger = logger
        self.output_dir = output_dir
        self.audio_file_path = os.path.join(output_dir, self.id, "audio.wav")
        os.makedirs(os.path.dirname(self.audio_file_path), exist_ok=True)

    @abc.abstractmethod
    def generate(self, manuscript: Manuscript) -> Audio:
        pass
