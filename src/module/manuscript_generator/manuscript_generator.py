import abc
import logging

from pydantic import BaseModel, Field


class Content(BaseModel):
    speaker_id: str = Field(
        description="話者を識別するIDであり、音声合成において異なる話者を割り当てるために利用する"
    )
    text: str = Field(description="各文章を表す。この文章は長くなりすぎてはいけない")
    links: list[str] = Field(description="文章内に含まれるリンクをすべて抽出したもの")


class Manuscript(BaseModel):
    title: str = Field(description="動画のタイトル")
    overview: str = Field(description="動画の概要文")
    keywords: list[str] = Field(description="動画のキーワードであり、コンマ区切りで5個")
    contents: list[Content] = Field(description="動画内で紹介される各文章の配列")
    meta: dict | None = Field(description="（GPTによる編集禁止）メタ情報")


class IManuscriptGenerator(metaclass=abc.ABCMeta):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        self.id = id
        self.logger = logger

    @abc.abstractmethod
    def generate(self) -> Manuscript:
        pass
