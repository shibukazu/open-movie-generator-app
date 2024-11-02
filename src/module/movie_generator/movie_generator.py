import abc
import logging
import os
import sys

from dotenv import load_dotenv

from ..audio_generator import Audio
from ..manuscript_generator import Manuscript

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import ResourceManager, UploadManager  # noqa: E402

current_dir = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

FONT_PATH = os.getenv("FONT_PATH")


class IMovieGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, is_short: bool, logger: logging.Logger) -> None:
        self.id = id
        self.logger = logger
        self.upload_manager = UploadManager(logger=logger)
        self.resource_manager = ResourceManager()
        self.font_path = FONT_PATH
        self.is_short = is_short

        self.output_movie_path = os.path.join(
            current_dir, "../../../output", self.id, "movie.mp4"
        )
        os.makedirs(os.path.dirname(self.output_movie_path), exist_ok=True)

    @abc.abstractmethod
    def generate(self, manuscript: Manuscript, audio: Audio) -> None:
        pass

    def skip(self) -> None:
        pass
