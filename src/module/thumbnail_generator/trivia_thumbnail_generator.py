import logging
import os
import sys
from typing import List

import requests
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

from .thumbnail_generator import IThumbnailGenerator as IThumbnailGenerator
from .thumbnail_generator import Manuscript

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import tokenize  # noqa: E402

load_dotenv()

FONT_PATH = os.getenv("FONT_PATH")

current_dir = os.path.dirname(os.path.abspath(__file__))


class Keywords(BaseModel):
    keywords: List[str]


class TriviaShortThumbnailGenerator(IThumbnailGenerator):
    def __init__(self, id: str, openai_apikey: str, logger: logging.Logger) -> None:
        super().__init__(id, logger)
        try:
            self.openai_client = OpenAI(api_key=openai_apikey)
        except ValueError as e:
            raise e

    def generate(self, manuscript: Manuscript) -> None:
        output_image_path = os.path.join(
            current_dir, "../../../output/", self.id, "thumbnail.png"
        )
        output_original_image_path = os.path.join(
            current_dir, "../../../output/", self.id, "thumbnail_original.png"
        )
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        os.remove(output_image_path) if os.path.exists(output_image_path) else None

        title = manuscript.title

        # 画像のサイズ設定
        width, height = 1080, 1920

        # 背景画像を生成する
        # manuscriptのキーワードは一部がOpenAIのSafety Policyに抵触する可能性があるため、一度厳選する
        filter_response = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": "作成している動画のキーワードが与えられます。このうち、DALL-Eを用いて動画のサムネイル画像を生成するにあたって有用かつDALL-Eの制約に抵触しないキーワードを抽出してください。例えば個人名や不適切な単語が抵触するキーワードです。",
                },
                {
                    "role": "user",
                    "content": f"{','.join(manuscript.keywords)}",
                },
            ],
            response_format=Keywords,
        )

        keywords = filter_response.choices[0].message.parsed
        if not keywords:
            raise ValueError(
                "サムネイル画像生成に用いるキーワードの抽出に失敗しました。"
            )

        image_generation_response = self.openai_client.images.generate(
            model="dall-e-3",
            prompt=f"{','.join(keywords.keywords)}",
            size="1024x1792",
            quality="standard",
            n=1,
        )

        background_image_url = image_generation_response.data[0].url
        if background_image_url is None:
            raise ValueError("DALL-Eでのサムネイル背景画像生成に失敗しました。")
        background_image_path = os.path.join(
            current_dir, "../../../output/", self.id, "original_background.png"
        )
        os.makedirs(os.path.dirname(background_image_path), exist_ok=True)
        os.remove(background_image_path) if os.path.exists(
            background_image_path
        ) else None
        response = requests.get(url=background_image_url)
        if response.status_code == 200:
            with open(background_image_path, "wb") as file:
                for chunk in response.iter_content(1024):  # 1KBごとに書き込み
                    file.write(chunk)
            self.logger.info(f"背景画像をダウンロードしました: {background_image_path}")
        else:
            raise ValueError(
                f"背景画像のダウンロードに失敗しました: {background_image_url}"
            )

        # 背景画像を開いてリサイズ
        background = Image.open(background_image_path).convert("RGBA")
        background = background.resize((width, height))
        draw = ImageDraw.Draw(background)

        # フォント設定
        font_size_title = 150
        font_title = ImageFont.truetype(FONT_PATH, font_size_title)

        # タイトルを描画
        num_text_per_line = width // font_size_title
        wrapped_titles = []
        line = ""
        for token in tokenize(title):
            if len(line) + len(token) >= num_text_per_line:
                wrapped_titles.append(line)
                line = ""
            line += token
        if line:
            wrapped_titles.append(line)

        # 上から順に描画
        y = 40
        for i, wrapped_title in enumerate(wrapped_titles):
            text_width, text_height = draw.textsize(wrapped_title, font=font_title)
            x = (width - text_width) // 2
            # 白い縁取りを描く（アンチエイリアス効果を強調）
            outline_width = 2
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text(
                            (x + dx, y + dy),
                            wrapped_title,
                            font=font_title,
                            fill=(255, 255, 255, 255),
                        )
            # タイトルを描写
            if (
                "navy" in background_image_path
                or "black" in background_image_path
                or "blue" in background_image_path
            ):
                title_color = (255, 215, 0, 255)
            else:
                # blue
                title_color = (0, 0, 128, 255)
            draw.text((x, y), wrapped_title, font=font_title, fill=title_color)
            y += text_height + 40

        # 後続の動画生成で使えるようにオリジナルサイズの画像も保存する
        background.save(output_original_image_path, quality=85)
        # ショート動画のアップロード用にミニサイズを生成する
        background = background.resize((540, 960), Image.ANTIALIAS)
        background.save(output_image_path, quality=85)
        self.logger.info(f"サムネイル画像を生成しました: {output_image_path}")
