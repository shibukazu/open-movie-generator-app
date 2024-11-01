import logging
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

from .thumbnail_generator import IThumbnailGenerator as IThumbnailGenerator
from .thumbnail_generator import Manuscript

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import ImageGenerator, tokenize  # noqa: E402

load_dotenv()

FONT_PATH = os.getenv("FONT_PATH")

current_dir = os.path.dirname(os.path.abspath(__file__))


class TriviaShortThumbnailGenerator(IThumbnailGenerator):
    def __init__(self, id: str, openai_apikey: str, logger: logging.Logger) -> None:
        super().__init__(id, logger)
        try:
            self.openai_client = OpenAI(api_key=openai_apikey)
        except ValueError as e:
            raise e
        self.image_generator = ImageGenerator(
            openai_apikey=openai_apikey, logger=logger
        )

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

        width, height = 1080, 1920

        background_image_path = os.path.join(
            current_dir, "../../../output/", self.id, "original_background.png"
        )
        self.image_generator.generate_from_keywords(
            keywords=manuscript.keywords,
            image_path=background_image_path,
            image_size="1024x1024",
        )
        background = Image.open(background_image_path).convert("RGBA")
        background = background.resize((1024, 1024))

        canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        x_offset = (width - background.width) // 2
        y_offset = (height - background.height) // 2
        canvas.paste(background, (x_offset, y_offset))

        font_size_title = 150
        font_title = ImageFont.truetype(FONT_PATH, font_size_title)

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

        draw = ImageDraw.Draw(canvas)

        text_width_top, text_height_top = draw.textsize(
            wrapped_titles[0], font=font_title
        )
        x_top = (width - text_width_top) // 2
        y_top = y_offset - text_height_top - 20
        draw.text((x_top, y_top), wrapped_titles[0], font=font_title, fill="black")

        if len(wrapped_titles) > 1:
            y_bottom = y_offset + background.height + 20
            for wrapped_title in wrapped_titles[1:]:
                text_width, text_height = draw.textsize(wrapped_title, font=font_title)
                x = (width - text_width) // 2
                draw.text((x, y_bottom), wrapped_title, font=font_title, fill="black")
                y_bottom += text_height + 10

        # 後続の動画生成で使えるようにオリジナルサイズの画像を保存する
        canvas.save(output_original_image_path, quality=85)
        # ショート動画のアップロード用にミニサイズをサムネイルとして保存する
        canvas = canvas.resize((540, 960), Image.ANTIALIAS)
        canvas.save(output_image_path, quality=85)
        self.logger.info(f"サムネイル画像を生成しました: {output_image_path}")
