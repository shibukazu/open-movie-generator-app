import abc
import logging
import os
import sys

from ..audio_generator import Audio
from ..manuscript_generator import Manuscript

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)


class IMovieGenerator(metaclass=abc.ABCMeta):
    def __init__(
        self,
        id: str,
        is_short: bool,
        logger: logging.Logger,
        font_path: str,
        output_dir: str,
    ) -> None:
        self.id = id
        self.logger = logger
        self.is_short = is_short
        self.font_path = font_path
        self.output_dir = output_dir
        self.output_movie_path = os.path.join(output_dir, self.id, "movie.mp4")
        os.makedirs(os.path.dirname(self.output_movie_path), exist_ok=True)

    @abc.abstractmethod
    def generate(self, manuscript: Manuscript, audio: Audio) -> None:
        pass
