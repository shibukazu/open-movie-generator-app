import abc
import logging
import os
import sys

from ..audio_generator import Audio
from ..manuscript_generator import Manuscript

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import UploadManager  # noqa: E402

current_dir = os.path.dirname(os.path.abspath(__file__))


class IMovieGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        self.id = id
        self.logger = logger
        self.upload_manager = UploadManager(logger=logger)

    @abc.abstractmethod
    def generate(self, manuscript: Manuscript, audio: Audio) -> None:
        pass

    def skip(self) -> None:
        pass
