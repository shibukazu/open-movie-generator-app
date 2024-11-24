import abc
import logging
import os
import sys

from ..manuscript_generator import Manuscript

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)


class IThumbnailGenerator(metaclass=abc.ABCMeta):
    def __init__(
        self,
        id: str,
        logger: logging.Logger,
        font_path: str,
        output_dir: str,
    ) -> None:
        self.id = id
        self.logger = logger
        self.font_path = font_path
        self.output_dir = output_dir
        self.output_thumbnail_path = os.path.join(output_dir, self.id, "thumbnail.png")
        os.makedirs(os.path.dirname(self.output_thumbnail_path), exist_ok=True)
        self.output_original_thumbnail_path = os.path.join(
            output_dir, self.id, "thumbnail_original.png"
        )
        os.makedirs(os.path.dirname(self.output_original_thumbnail_path), exist_ok=True)

    @abc.abstractmethod
    def generate(
        self,
        manuscript: Manuscript,
    ) -> None:
        pass

    def skip(self) -> None:
        pass
