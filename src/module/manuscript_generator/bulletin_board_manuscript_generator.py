import logging
import re
from typing import Literal

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel, Field

from .manuscript_generator import Content, IManuscriptGenerator, Manuscript

# クレンジング用の正規表現
REG_EMOJI = re.compile(
    r"[\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF]",
    re.UNICODE,
)
REG_LINKS = [
    re.compile(r"https?:\/\/[-_.!~*'()a-zA-Z0-9;\/?:\@&=+\$.,%#]+", re.UNICODE),
    re.compile(r"http?:\/\/[-_.!~*'()a-zA-Z0-9;\/?:\@&=+\$.,%#]+", re.UNICODE),
    re.compile(r"www\.[a-zA-Z0-9;\/?:\@&=+\$.,%#]+", re.UNICODE),
]


class RawManuscript(BaseModel):
    contents: list[Content] = Field()
    meta: dict = Field()


class BulletinBoardManuscriptGenerator(IManuscriptGenerator):
    def __init__(
        self, id: str, openai_apikey: str, source_url: str, logger: logging.Logger
    ) -> None:
        super().__init__(id, logger)

        try:
            self.source_url_type: Literal["nova"] = get_url_type(source_url)
            self.source_url = source_url
            self.openai_client = OpenAI(api_key=openai_apikey)
        except ValueError as e:
            raise e

    def generate(self) -> Manuscript:
        raw_manuscript: RawManuscript
        if self.source_url_type == "nova":
            self.logger.info("5ch novaからスレッドの内容を取得します")
            raw_manuscript = self.generate_raw_manuscript_from_nova()
        else:
            raise NotImplementedError(
                f"サポートされていないURLタイプです: {self.source_url_type}"
            )
        self.logger.debug(raw_manuscript)
        self.logger.info("スレッドの内容をクレンジングします")
        manuscript = self.cleansing_raw_manuscript(raw_manuscript)
        self.logger.debug(manuscript)

        dump = manuscript.model_dump_json()
        with open(self.dump_file_path, "w") as f:
            f.write(dump)
        return manuscript

    def generate_raw_manuscript_from_nova(self) -> RawManuscript:
        response = requests.get(self.source_url)
        response.encoding = "shift_jis"

        soup = BeautifulSoup(response.text, "html.parser")
        raw_manuscript = RawManuscript(
            contents=[],
            meta={
                "type": "bulletin_board",
                "original_link": self.source_url,
                "thread_title": soup.find("h1", id="threadtitle").text,
            },
        )

        comments = soup.find_all("article", class_="clear post")
        for comment in comments:
            user_id = comment.get("data-userid")
            text = comment.find("section", class_="post-content").text

            raw_manuscript.contents.append(
                Content(
                    speaker_id=user_id,
                    text=text,
                    links=[],
                )
            )

        return raw_manuscript

    def cleansing_raw_manuscript(self, raw_manuscript: RawManuscript) -> Manuscript:
        # GPTによるデータクレンジング&補完
        json_raw_manuscript = raw_manuscript.model_dump_json()
        completion = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": "与えられたJSON形式のコメント一覧から、スレッドのタイトルに関連する重要なコメントを抽出してください。コメントは必ず15件以上抽出してください。",
                },
                {
                    "role": "system",
                    "content": "YouTubeにおいて不適切なコメントは除外してください。",
                },
                {
                    "role": "system",
                    "content": "動画概要を口語調で生成し、概要には「今日の動画では〇〇を紹介します。」という形式を守ってください。",
                },
                {
                    "role": "system",
                    "content": "動画のタイトルは20文字以内で生成し、keywordsも5つ考えてください。",
                },
                {"role": "user", "content": json_raw_manuscript},
            ],
            response_format=Manuscript,
        )

        manuscript = completion.choices[0].message.parsed
        if not manuscript:
            raise Exception("GPT-4oによるクレンジングに失敗しました。")

        manuscript.meta = raw_manuscript.meta

        # ルールベースでのクレンジング
        for content in manuscript.contents:
            # 本文のクレンジング
            content.text = content.text.strip()
            content.text = re.sub(r"^>>\d+", "", content.text).strip()
            content.text = REG_EMOJI.sub("", content.text)

            # リンク抽出とクレンジング
            links = []
            for reg_link in REG_LINKS:
                matched_links = reg_link.findall(content.text)
                if matched_links:
                    links.extend(matched_links)
                    content.text = reg_link.sub("", content.text)
            content.text = content.text.strip()
            content.links = links

            if not content.text:
                manuscript.contents.remove(content)

        self.logger.info("掲示板に基づいた原稿を生成しました")

        return manuscript


def get_url_type(url: str) -> Literal["nova"]:
    if url.startswith("https://nova.5ch.net/test/read.cgi/"):
        return "nova"
    else:
        raise ValueError("URLが無効です。正しいURLを指定してください。")
