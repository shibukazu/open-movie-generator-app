import logging
import os
import sys
from logging import getLogger

import flet as ft
from matplotlib import font_manager

from src.command.bulletin import bulletin_cmd
from src.module.audio_generator import IAudioGenerator
from src.module.manuscript_generator import (
    IManuscriptGenerator,
)
from src.module.movie_generator import (
    IMovieGenerator,
)
from src.module.thumbnail_generator import (
    IThumbnailGenerator,
)
from src.util.flet import file_picker_row

logger = getLogger(__name__)
logging.basicConfig(level=logging.INFO)


SCRIPT_PATH = (
    os.path.join(os.getcwd(), "script/install.sh")
    if not hasattr(sys, "_MEIPASS")
    else os.path.join(sys._MEIPASS, "script/install.sh")
)

LIB_PATH = (
    os.path.join(os.getcwd(), "lib")
    if not hasattr(sys, "_MEIPASS")
    else os.path.join(sys._MEIPASS, "lib")
)


FONTS = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
FONT_MAP = {}
for path in FONTS:
    try:
        font_name = font_manager.FontProperties(fname=path).get_name()
        FONT_MAP[font_name] = path
    except RuntimeError:
        pass


def main(page: ft.Page) -> None:
    page.title = "Shoorter"
    page.scroll = "adaptive"

    page.add(app(page))


def app(page: ft.Page) -> ft.Stack:
    openai_apikey_input = ft.TextField(
        label="OpenAI APIキー",
        hint_text="OpenAIのAPIキーを入力してください",
        width=400,
    )

    font_path_select = ft.Dropdown(
        label="フォントを選択",
        options=[ft.dropdown.Option(font_name) for font_name in FONT_MAP.keys()],
        value="YuMincho" if "YuMincho" in FONT_MAP.keys() else None,
        width=400,
    )

    output_dir_row, output_dir_item = file_picker_row(
        page, is_directory=True, label="出力先ディレクトリ:"
    )

    common_setting_column = ft.Column(
        [
            ft.Text("共通設定", size=24, weight="bold"),
            openai_apikey_input,
            font_path_select,
            output_dir_row,
        ],
        spacing=10,
        scroll="adaptive",
    )

    bulletin_setting_column = bulletin_setting(
        page=page,
        openai_api_key_input=openai_apikey_input,
        font_path_select=font_path_select,
        output_dir_item=output_dir_item,
    )

    log_output_column = log_output(page)

    return ft.Column(
        [
            common_setting_column,
            ft.Divider(),
            bulletin_setting_column,
            ft.Divider(),
            log_output_column,
        ],
        spacing=10,
        scroll="adaptive",
        expand=True,
    )


def log_output(page: ft.Page) -> ft.Column:
    class FletLogHandler(logging.Handler):
        def __init__(self, log_output: ft.Text, page: ft.Page):
            super().__init__()
            self.log_output = log_output
            self.page = page

        def emit(self, record: logging.LogRecord) -> None:
            log_entry = self.format(record)
            self.log_output.value += f"\n{log_entry}"
            self.page.update()

    log_output = ft.Text(
        value="",
        size=14,
        selectable=True,
        expand=True,
    )
    log_handler = FletLogHandler(log_output, page)
    logger.addHandler(log_handler)
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)

    column = ft.Column(
        [
            ft.Text(
                "ログ",
                size=24,
                weight="bold",
            ),
            log_output,
        ],
        expand=True,
    )

    return column


def bulletin_setting(
    page: ft.Page,
    openai_api_key_input: ft.TextField,
    output_dir_item: ft.Text,
    font_path_select: ft.Dropdown,
) -> ft.Column:
    # フォームの構成
    theme_input = ft.TextField(
        label="テーマ",
        hint_text="議論させたいテーマを入力してください",
        width=400,
    )

    man_image_dir_row, man_image_dir_item = file_picker_row(
        page, is_directory=True, label="男性画像ディレクトリ:"
    )

    woman_image_dir_row, woman_image_dir_item = file_picker_row(
        page, is_directory=True, label="女性画像ディレクトリ:"
    )

    bgm_image_dir_row, bgm_image_dir_item = file_picker_row(
        page, is_directory=False, label="BGMファイル:"
    )

    bgv_image_dir_row, bgv_image_dir_item = file_picker_row(
        page, is_directory=False, label="背景動画ファイル:"
    )

    error_message = ft.Text("", color="red")
    page.snack_bar = ft.SnackBar(
        content=error_message,
    )
    progress_bar = ft.ProgressBar(visible=False, width=400)
    progress_bar_label = ft.Text(visible=False)

    def generate_video(e: ft.ControlEvent) -> None:
        try:
            onnxruntime_lib_path = "/libonnxruntime.dylib"
            open_jtalk_dict_dir_path = "/open_jtalk_dic_utf_8-1.11"
            if not all(
                [
                    theme_input.value,
                    openai_api_key_input.value,
                    onnxruntime_lib_path,
                    open_jtalk_dict_dir_path,
                    man_image_dir_item.value,
                    woman_image_dir_item.value,
                    bgm_image_dir_item.value,
                    bgv_image_dir_item.value,
                    font_path_select.value,
                ]
            ):
                raise ValueError("全ての項目を入力してください。")

            (
                manuscript_genetrator,
                audio_generator,
                thumbnail_generator,
                movie_generator,
            ) = bulletin_cmd(
                themes=[theme_input.value],
                openai_api_key=openai_api_key_input.value,
                output_dir=output_dir_item.value,
                onnxruntime_lib_path=onnxruntime_lib_path,
                open_jtalk_dict_dir_path=open_jtalk_dict_dir_path,
                man_image_dir=man_image_dir_item.value,
                woman_image_dir=woman_image_dir_item.value,
                bgm_file_path=bgm_image_dir_item.value,
                bgv_file_path=bgv_image_dir_item.value,
                font_path=FONT_MAP[font_path_select.value],
                logger=logger,
            )
            pipeline(
                page=page,
                progress_bar=progress_bar,
                progress_bar_label=progress_bar_label,
                action_button=action_button,
                error_message=error_message,
                manuscript_genetrator=manuscript_genetrator,
                audio_generator=audio_generator,
                thumbnail_generator=thumbnail_generator,
                movie_generator=movie_generator,
            )
        except Exception as e:
            error_message.value = f"エラーが発生しました: {str(e)}"
            page.snack_bar.open = True
            page.update()

    action_button = ft.ElevatedButton(text="動画生成", on_click=generate_video)

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("掲示板風動画生成", size=24, weight="bold"),
                    action_button,
                ],
                alignment="spaceBetween",
            ),
            ft.Row(
                [
                    progress_bar_label,
                    progress_bar,
                ],
                alignment="start",
                spacing=5,
            ),
            theme_input,
            man_image_dir_row,
            woman_image_dir_row,
            bgm_image_dir_row,
            bgv_image_dir_row,
        ],
        spacing=10,
        scroll="adaptive",
    )


def pipeline(
    page: ft.Page,
    progress_bar: ft.ProgressBar,
    progress_bar_label: ft.Text,
    action_button: ft.ElevatedButton,
    error_message: ft.Text,
    manuscript_genetrator: IManuscriptGenerator,
    audio_generator: IAudioGenerator,
    thumbnail_generator: IThumbnailGenerator,
    movie_generator: IMovieGenerator,
) -> None:
    try:
        progress_bar.visible = True
        progress_bar.value = 0
        progress_bar_label.visible = True
        action_button.visible = False
        page.update()

        logger.info("Step1: 原稿生成")
        try:
            progress_bar_label.value = "原稿生成中..."
            page.update()

            manuscript = manuscript_genetrator.generate()

            progress_bar.value = 0.25
            page.update()
        except Exception as e:
            logger.error(f"原稿生成中にエラーが発生しました。 {e}")
            raise Exception(f"原稿生成中にエラーが発生しました。 {e}")

        logger.info("Step2: 音声合成")
        try:
            progress_bar_label.value = "音声合成中..."
            page.update()

            audio = audio_generator.generate(manuscript)

            progress_bar.value = 0.5
            page.update()
        except Exception as e:
            logger.error(f"音声合成中にエラーが発生しました。 {e}")
            raise Exception(f"音声合成中にエラーが発生しました。 {e}")

        logger.info("Step3: サムネイル生成")
        try:
            progress_bar_label.value = "サムネイル生成中..."
            page.update()

            thumbnail_generator.generate(manuscript)

            progress_bar.value = 0.75
            page.update()
        except Exception as e:
            logger.error(f"サムネイル生成中にエラーが発生しました。 {e}")
            raise Exception(f"サムネイル生成中にエラーが発生しました。 {e}")

        logger.info("Step4: 動画生成")
        try:
            progress_bar_label.value = "動画生成中..."
            page.update()

            movie_generator.generate(manuscript, audio)

            progress_bar.value = 1
            page.update()
        except Exception as e:
            logger.error(f"動画生成中にエラーが発生しました。 {e}")
            raise Exception(f"動画生成中にエラーが発生しました。 {e}")

        logger.info("すべてのステップを正常に終了しました")
        progress_bar.visible = False
        progress_bar_label.visible = False
        action_button.visible = True
        page.update()

    except Exception as e:
        progress_bar.visible = False
        progress_bar_label.visible = False
        action_button.visible = True
        error_message.value = f"エラーが発生しました。 {str(e)}"
        page.snack_bar.open = True
        page.update()


ft.app(target=main, assets_dir="assets")
