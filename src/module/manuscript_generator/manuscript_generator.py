import abc
import logging
import os

from pydantic import BaseModel, Field

current_dir = os.path.dirname(os.path.abspath(__file__))


class Content(BaseModel):
    speaker_id: str = Field(
        description="（GPTによる編集禁止）話者IDであり、音声合成に利用する"
    )
    text: str = Field(description="文章")
    links: list[str] = Field(description="文章内に含まれるリンク")


class Manuscript(BaseModel):
    title: str = Field(description="タイトル")
    overview: str = Field(description="概要")
    keywords: list[str] = Field(description="動画のキーワードであり、コンマ区切りで5個")
    contents: list[Content] = Field(description="少なくとも40個以上の文章")
    meta: dict | None = Field(description="（GPTによる編集禁止）メタ情報")


class IManuscriptGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        self.id = id
        self.logger = logger
        self.dump_file_path = os.path.join(
            current_dir, "../../../output", self.id, "manuscript.json"
        )
        os.makedirs(os.path.dirname(self.dump_file_path), exist_ok=True)

    def skip(self) -> Manuscript:
        if not os.path.exists(self.dump_file_path):
            raise FileNotFoundError(
                f"Manuscript dump file not found: {self.dump_file_path}"
            )
        with open(self.dump_file_path, "r") as f:
            dump = f.read()
        manuscript = Manuscript.model_validate_json(dump)
        return manuscript

    @abc.abstractmethod
    def generate(self) -> Manuscript:
        pass
