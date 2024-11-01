import abc
import logging
import os
import sys

from dotenv import load_dotenv

from ..manuscript_generator import Manuscript

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import ResourceManager  # noqa: E402

load_dotenv()

FONT_PATH = os.getenv("FONT_PATH")

current_dir = os.path.dirname(os.path.abspath(__file__))


class IThumbnailGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, is_short: bool, logger: logging.Logger) -> None:
        self.id = id
        self.logger = logger
        self.is_short = is_short
        self.resource_manager = ResourceManager()
        self.font_path = FONT_PATH

    @abc.abstractmethod
    def generate(
        self,
        manuscript: Manuscript,
    ) -> None:
        pass

    def skip(self) -> None:
        pass
