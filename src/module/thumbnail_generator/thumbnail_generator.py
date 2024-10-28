import abc
import logging
import os

from ..manuscript_generator import Manuscript

current_dir = os.path.dirname(os.path.abspath(__file__))


class IThumbnailGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        self.id = id
        self.logger = logger

    @abc.abstractmethod
    def generate(
        self,
        manuscript: Manuscript,
    ) -> None:
        pass

    def skip(self) -> None:
        pass
