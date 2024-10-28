import logging
import os
import random
import textwrap

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from .thumbnail_generator import IThumbnailGenerator as IThumbnailGenerator
from .thumbnail_generator import Manuscript

load_dotenv()

FONT_PATH = os.getenv("FONT_PATH")

current_dir = os.path.dirname(os.path.abspath(__file__))


image_dir = os.path.join(current_dir, "../../../material/image/irasutoya")
image_file_list = [
    os.path.join(image_dir, f)
    for f in os.listdir(image_dir)
    if os.path.isfile(os.path.join(image_dir, f))
]
if len(image_file_list) == 0:
    raise FileNotFoundError(
        f"次のディレクトリ内にいらすとや画像が見つかりません: {image_dir}"
    )
image_path = random.choice(image_file_list)

background_dir = os.path.join(current_dir, "../../../material/image/background")
background_file_list = [
    os.path.join(background_dir, f)
    for f in os.listdir(background_dir)
    if os.path.isfile(os.path.join(background_dir, f))
]
if len(background_file_list) == 0:
    raise FileNotFoundError(
        f"次のディレクトリ内に背景画像が見つかりません: {background_dir}"
    )
background_image_path = random.choice(background_file_list)


class BulletinBoardShortThumbnailGenerator(IThumbnailGenerator):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        super().__init__(id, logger)

    def generate(self, manuscript: Manuscript) -> None:
        output_image_path = os.path.join(
            current_dir, "../../../output/", self.id, "thumbnail.png"
        )
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        os.remove(output_image_path) if os.path.exists(output_image_path) else None

        title = manuscript.title

        # 画像のサイズ設定
        width, height = 1080, 1920

        # 背景画像を開いてリサイズ
        background = Image.open(background_image_path).convert("RGBA")
        background = background.resize((width, height))
        draw = ImageDraw.Draw(background)

        # フォント設定
        font_size_title = 200
        font_title = ImageFont.truetype(FONT_PATH, font_size_title)

        # キャラクター画像を左下に配置
        image = (
            Image.open(image_path)
            .convert("RGBA")
            .resize((int(width * 0.5), int(height * 0.5)))
        )
        char_x = 0
        char_y = height - image.height

        # 前面にキャラクター画像を合成
        background.alpha_composite(image, (char_x, char_y))

        # タイトルを描画
        wrapped_titles = textwrap.wrap(title, width=width // font_size_title)

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
            y += text_height

        # 画像を保存または表示
        background.save(output_image_path)

        pass
