import logging
import os
import random
import sys
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as ImageClass
from PIL.ImageFont import FreeTypeFont

from .thumbnail_generator import IThumbnailGenerator as IThumbnailGenerator
from .thumbnail_generator import Manuscript

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from util import wrap_text  # noqa: E402

current_dir = os.path.dirname(os.path.abspath(__file__))


class BulletinBoardLongThumbnailGenerator(IThumbnailGenerator):
    def __init__(self, id: str, logger: logging.Logger) -> None:
        super().__init__(id, False, logger)

    def calc_contrast_color(self, image_path: str) -> Tuple[int, int, int]:
        image = Image.open(image_path)
        image = image.resize((100, 100))
        image = image.convert("RGB")

        # ピクセルごとの色を取得
        pixels = list(image.getdata())
        from collections import Counter

        color_counts = Counter(pixels)
        main_color_rgb = color_counts.most_common(1)[0][0]
        contrast_color_rgb = (
            255 - main_color_rgb[0],
            255 - main_color_rgb[1],
            255 - main_color_rgb[2],
        )

        return contrast_color_rgb

    def draw_comment_board(
        self,
        background: ImageClass,
        id_text: str,
        id_font: FreeTypeFont,
        wrapped_texts: List[str],
        text_font: FreeTypeFont,
        position: Tuple[int, int],
    ) -> ImageClass:
        comment_board_width = background.size[0] // 2
        # 描画用のテンポラリイメージを作成（アンチエイリアスのため拡大）
        temp_image = Image.new("RGBA", background.size, (255, 255, 255, 0))
        temp_draw = ImageDraw.Draw(temp_image)
        text_height = temp_draw.textsize(wrapped_texts[0], font=text_font)[1]
        id_height = temp_draw.textsize(id_text, font=id_font)[1]
        padding = 10

        board_height = (text_height * len(wrapped_texts)) + id_height + 3 * padding

        x, y = position
        temp_draw.rectangle(
            [x, y, x + comment_board_width, y + board_height],
            fill=(255, 255, 224, 255),
            outline=(0, 0, 0),
            width=2,
        )

        id_x = x + padding
        id_y = y + padding
        temp_draw.text((id_x, id_y), id_text, font=id_font, fill=(0, 0, 0, 255))

        text_x = x + padding
        text_y = id_y + id_height + padding
        for text in wrapped_texts:
            temp_draw.text((text_x, text_y), text, font=text_font, fill=(0, 0, 0, 255))
            text_y += text_height

        # アンチエイリアス効果のために縮小して貼り付け
        new_background = background.copy()
        new_background.alpha_composite(temp_image)

        return new_background

    def draw_character(
        self,
        background: ImageClass,
        character_image_path: str,
    ) -> ImageClass:
        width, height = background.size

        character_image = Image.open(character_image_path).convert("RGBA")
        character_image = character_image.resize((int(width * 0.3), int(height * 0.5)))
        char_x = width - character_image.width - 20
        char_y = (height - character_image.height) // 2

        new_background = background.copy()
        new_background.alpha_composite(character_image, (char_x, char_y))
        return new_background

    def draw_title(
        self,
        background: ImageClass,
        wrapped_titles: List[str],
        title_font: FreeTypeFont,
        title_color: Tuple[int, int, int],
    ) -> ImageClass:
        width, height = background.size
        temp_image = Image.new("RGBA", background.size, (255, 255, 255, 0))
        temp_draw = ImageDraw.Draw(temp_image)
        text_width, text_height = temp_draw.textsize(wrapped_titles[0], font=title_font)
        x = (width - text_width) // 2
        y = 40
        # 白い縁取りを描く
        outline_width = 2
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    temp_draw.text(
                        (x + dx, y + dy),
                        wrapped_titles[0],
                        font=title_font,
                        fill=(255, 255, 255, 255),
                    )
        temp_draw.text((x, y), wrapped_titles[0], font=title_font, fill=title_color)

        if len(wrapped_titles) > 1:
            y = height - text_height - 40
            for wrapped_title in wrapped_titles[1:]:
                x = (width - text_width) // 2
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx != 0 or dy != 0:
                            temp_draw.text(
                                (x + dx, y + dy),
                                wrapped_title,
                                font=title_font,
                                fill=(255, 255, 255, 255),
                            )
                temp_draw.text((x, y), wrapped_title, font=title_font, fill=title_color)
                y -= text_height + 10

        new_background = background.copy()
        new_background.alpha_composite(temp_image)
        return new_background

    def generate(self, manuscript: Manuscript) -> None:
        background_image_path = self.resource_manager.random_background_image_path()
        character_image_path = self.resource_manager.random_character_image_path()

        width, height = 1920, 1080

        title = manuscript.title
        title_font_size = 150
        wrapped_titles = wrap_text(title, width // title_font_size)
        contents = manuscript.contents
        content1 = random.choice(contents)
        content2 = random.choice(contents)
        while content1.text == content2.text:
            content2 = random.choice(contents)
        comment_font_size = 50
        id_font_size = 40
        wrapped_text1s = wrap_text(content1.text, width // 2 // comment_font_size)
        wrapped_text2s = wrap_text(content2.text, width // 2 // comment_font_size)

        # 背景の設定
        background = Image.open(background_image_path).convert("RGBA")
        background = background.resize((width, height))

        # フォント設定
        title_font = ImageFont.truetype(self.font_path, title_font_size)
        comment_font = ImageFont.truetype(self.font_path, comment_font_size)
        id_font = ImageFont.truetype(self.font_path, id_font_size)

        # コメントボードを描画
        background = self.draw_comment_board(
            background=background,
            id_text=content1.speaker_id,
            id_font=id_font,
            wrapped_texts=wrapped_text1s,
            text_font=comment_font,
            position=(20, height // 3),
        )
        background = self.draw_comment_board(
            background=background,
            id_text=content2.speaker_id,
            id_font=id_font,
            wrapped_texts=wrapped_text2s,
            text_font=comment_font,
            position=(20, height // 3 + 250),
        )

        # キャラクターを描画
        background = self.draw_character(
            background=background,
            character_image_path=character_image_path,
        )

        # タイトルを描画
        title_color = self.calc_contrast_color(background_image_path)
        background = self.draw_title(
            background=background,
            wrapped_titles=wrapped_titles,
            title_font=title_font,
            title_color=title_color,
        )

        # 後続の動画生成で使えるようにオリジナルサイズの画像を保存する
        background.save(self.output_original_thumbnail_path, quality=85)
        # ショート動画のアップロード用にミニサイズをサムネイルとして保存する
        background = background.resize((width // 2, height // 2), Image.ANTIALIAS)
        background.save(self.output_thumbnail_path, quality=85)

        self.logger.info(
            f"掲示板形式のサムネイルを生成しました　縮小版: {self.output_thumbnail_path}"
        )
        self.logger.info(
            f"掲示板形式のサムネイルを生成しました　オリジナル版: {self.output_original_thumbnail_path}"
        )
