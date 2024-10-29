import logging
import os
import random
import textwrap
from typing import List, Literal, Tuple

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

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
woman_image_file_list = [
    image_file for image_file in image_file_list if "_woman_" in image_file
]
if len(woman_image_file_list) == 0:
    raise FileNotFoundError(
        f"次のディレクトリ内に女性の画像が必要です。なお、女性画像のファイル名には_woman_を含めてください。: {image_dir}"
    )
man_image_file_list = [
    image_file for image_file in image_file_list if "_man_" in image_file
]
if len(man_image_file_list) == 0:
    raise FileNotFoundError(
        f"次のディレクトリ内に男性の画像が必要です。なお、男性画像のファイル名には_man_を含めてください。: {image_dir}"
    )
woman_image_path = random.choice(woman_image_file_list)
man_image_path = random.choice(man_image_file_list)

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


class BulletinBoardThumbnailGenerator(IThumbnailGenerator):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        super().__init__(id, logger)

    def generate(self, manuscript: Manuscript) -> None:
        output_image_path = os.path.join(
            current_dir, "../../../output/", self.id, "thumbnail.png"
        )
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        os.remove(output_image_path) if os.path.exists(output_image_path) else None

        title = manuscript.title
        contents = manuscript.contents
        content1 = random.choice(contents)
        text1 = content1.text
        content2 = random.choice(contents)
        text2 = content2.text
        while text1 == text2:
            text2 = random.choice(contents).text
        splitted_text1 = textwrap.wrap(text1, 25)
        splitted_text2 = textwrap.wrap(text2, 25)

        # 画像のサイズ設定
        width, height = 1280, 720

        # 背景画像を開いてリサイズ
        background = Image.open(background_image_path).convert("RGBA")
        background = background.resize((width, height))
        draw = ImageDraw.Draw(background)

        # フォント設定
        font_size_title = 60
        font_size_comment = 35
        font_size_id = 25
        font_title = ImageFont.truetype(FONT_PATH, font_size_title)
        font_comment = ImageFont.truetype(FONT_PATH, font_size_comment)
        font_id = ImageFont.truetype(FONT_PATH, font_size_id)

        def draw_text_with_board(
            draw: ImageDraw,
            splitted_text: List[str],
            position: Tuple[int, int],
            font: FreeTypeFont,
            fill: Tuple[Literal[0], Literal[0], Literal[0], Literal[255]],
            id_text: str,
        ) -> None:
            # 描画用のテンポラリイメージを作成（アンチエイリアスのため拡大）
            temp_image = Image.new("RGBA", background.size, (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_image)

            max_text_width = max(
                temp_draw.textsize(line, font=font)[0] for line in splitted_text
            )
            text_height = temp_draw.textsize(splitted_text[0], font=font)[1]
            id_width, id_height = temp_draw.textsize(id_text, font=font_id)
            padding = 10
            board_width = max_text_width + 2 * padding
            board_height = (text_height * len(splitted_text)) + id_height + 3 * padding

            x, y = position
            temp_draw.rectangle(
                [x, y, x + board_width, y + board_height],
                fill=(255, 255, 224, 255),
                outline=(0, 0, 0),
                width=2,
            )

            id_x = x + padding
            id_y = y + padding
            temp_draw.text((id_x, id_y), id_text, font=font_id, fill=(0, 0, 0, 255))

            text_x = x + padding
            text_y = id_y + id_height + padding
            for text in splitted_text:
                temp_draw.text((text_x, text_y), text, font=font, fill=fill)
                text_y += text_height

            # アンチエイリアス効果のために縮小して貼り付け
            background.alpha_composite(temp_image)

        # コメントボードを描画
        draw_text_with_board(
            draw,
            splitted_text1,
            (20, height // 3),
            font_comment,
            fill=(0, 0, 0, 255),
            id_text=content1.speaker_id,
        )
        draw_text_with_board(
            draw,
            splitted_text2,
            (20, height // 3 + 200),
            font_comment,
            fill=(0, 0, 0, 255),
            id_text=content2.speaker_id,
        )

        # キャラクター画像を右端に配置
        man_image = Image.open(man_image_path).convert("RGBA")
        man_image = man_image.resize((int(width * 0.3), int(height * 0.5)))
        char_x = width - man_image.width - 20
        char_y = (height - man_image.height) // 2

        # 女性キャラクター画像を左下に部分的に重ねる
        woman_image = Image.open(woman_image_path).convert("RGBA")
        woman_image = woman_image.resize((int(width * 0.2), int(height * 0.3)))
        woman_x = char_x - int(woman_image.width * 0.4)
        woman_y = char_y + man_image.height - woman_image.height

        # 背面に女性画像を合成
        background.alpha_composite(woman_image, (woman_x, woman_y))

        # 前面に男性画像を合成
        background.alpha_composite(man_image, (char_x, char_y))

        # タイトルを描画
        wrapped_title = textwrap.wrap(title, width=18)

        # タイトルを上端に配置
        top_y = 40
        line = wrapped_title[0]
        text_width, text_height = draw.textsize(line, font=font_title)
        x = (width - text_width) // 2
        y = top_y

        # 白い縁取りを描く（アンチエイリアス効果を強調）
        outline_width = 2
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text(
                        (x + dx, y + dy),
                        line,
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
        draw.text((x, y), line, font=font_title, fill=title_color)

        if len(wrapped_title) > 1:
            # タイトルを下端に配置
            bottom_y = height - text_height * len(wrapped_title) - 40
            line = wrapped_title[1]
            text_width, text_height = draw.textsize(line, font=font_title)
            x = (width - text_width) // 2
            y = bottom_y + (text_height + 10)

            # 白い縁取りを描く（アンチエイリアス効果を強調）
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text(
                            (x + dx, y + dy),
                            line,
                            font=font_title,
                            fill=(255, 255, 255, 255),
                        )

            # 金色のタイトルを描く
            draw.text((x, y), line, font=font_title, fill=(255, 215, 0, 255))

        # 画像を保存または表示
        background.save(output_image_path)

        pass
