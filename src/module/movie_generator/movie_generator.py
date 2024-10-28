import abc
import logging
import os

from ..audio_generator import Audio
from ..manuscript_generator import Manuscript

current_dir = os.path.dirname(os.path.abspath(__file__))


class IMovieGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        self.id = id
        self.logger = logger

    @abc.abstractmethod
    def generate(self, manuscript: Manuscript, audio: Audio) -> None:
        pass

    def skip(self) -> None:
        pass
