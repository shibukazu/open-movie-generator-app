import logging
import os
from typing import List, Literal

import requests
from openai import OpenAI
from pydantic import BaseModel


class Keywords(BaseModel):
    keywords: List[str]


class ImageGenerator:
    def __init__(
        self,
        openai_apikey: str,
        logger: logging.Logger,
    ):
        self.logger = logger
        try:
            self.openai_client = OpenAI(api_key=openai_apikey)
        except ValueError as e:
            raise e

    def __filter_keywords(self, keywords: List[str]) -> List[str]:
        filter_response = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": "OpenAI Usage policiesを参照して、Policyに抵触しないキーワードを抽出してください。例えば個人名や不適切な単語が抵触するキーワードです。",
                },
                {
                    "role": "user",
                    "content": f"{','.join(keywords)}",
                },
            ],
            response_format=Keywords,
        )
        filtered_keywords = filter_response.choices[0].message.parsed
        if not filtered_keywords:
            raise ValueError("画像生成に用いるキーワードの抽出に失敗しました。")
        return filtered_keywords.keywords

    def __extract_and_filter_keywords(self, text: str) -> List[str]:
        filter_response = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": "DALL-Eを用いた画像生成において効果的なキーワードをできるだけたくさん抽出してください。",
                },
                {
                    "role": "system",
                    "content": "また、OpenAI Usage policiesを参照して、Policyに触れるようなキーワードは除外してください。例えば個人名や危険な単語などです。",
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
            response_format=Keywords,
        )
        filtered_keywords = filter_response.choices[0].message.parsed
        if not filtered_keywords:
            raise ValueError("画像生成に用いるキーワードの抽出に失敗しました。")
        return filtered_keywords.keywords

    def generate_from_keywords(
        self,
        keywords: List[str],
        image_path: str,
        image_size: Literal[
            "256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"
        ],
    ) -> None:
        filtered_keywords = self.__filter_keywords(keywords)
        self.logger.info(f"フィルター後キーワード一覧: {filtered_keywords}")
        if len(filtered_keywords) == 0:
            self.logger.info(
                "フィルター後キーワードが空のため、動画というキーワードで生成を試みます"
            )
            filtered_keywords = ["動画"]
        try:
            image_generation_response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=f"{','.join(filtered_keywords)}",
                size=image_size,
                quality="standard",
                n=1,
            )
        except Exception as e:
            self.logger.error(f"画像生成に失敗しました: {e}")
            self.logger.info("代わりに動画というキーワードで生成を試みます")
            image_generation_response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt="動画",
                size=image_size,
                quality="standard",
                n=1,
            )
        image_url = image_generation_response.data[0].url
        if image_url is None:
            raise ValueError("DALL-Eでの画像生成に失敗しました。")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        os.remove(image_path) if os.path.exists(image_path) else None
        response = requests.get(url=image_url)
        if response.status_code == 200:
            with open(image_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            self.logger.info(f"画像を保存しました: {image_path}")
        else:
            raise ValueError(f"画像のダウンロードに失敗しました: {image_url}")

    def generate_from_text(
        self,
        text: str,
        image_path: str,
        image_size: Literal[
            "256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"
        ],
    ) -> None:
        filtered_keywords = self.__extract_and_filter_keywords(text)
        self.logger.info(f"フィルター後キーワード一覧: {filtered_keywords}")
        if len(filtered_keywords) == 0:
            self.logger.info(
                "フィルター後キーワードが空のため、動画というキーワードで生成を試みます"
            )
            filtered_keywords = ["動画"]
        try:
            image_generation_response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=f"{','.join(filtered_keywords)}",
                size=image_size,
                quality="standard",
                n=1,
            )
        except Exception as e:
            self.logger.error(f"画像生成に失敗しました: {e}")
            self.logger.info("代わりに動画というキーワードで生成を試みます")
            image_generation_response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt="動画",
                size=image_size,
                quality="standard",
                n=1,
            )
        image_url = image_generation_response.data[0].url
        if image_url is None:
            raise ValueError("DALL-Eでの画像生成に失敗しました。")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        os.remove(image_path) if os.path.exists(image_path) else None
        response = requests.get(url=image_url)
        if response.status_code == 200:
            with open(image_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            self.logger.info(f"画像を保存しました: {image_path}")
        else:
            raise ValueError(f"画像のダウンロードに失敗しました: {image_url}")
