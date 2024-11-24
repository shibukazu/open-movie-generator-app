import logging
import os
import subprocess
import sys
import threading
from logging import getLogger
from typing import Callable

import flet as ft
from matplotlib import font_manager

from command.bulletin import bulletin_cmd
from module.audio_generator import IAudioGenerator
from module.manuscript_generator import (
    IManuscriptGenerator,
)
from module.movie_generator import (
    IMovieGenerator,
)
from module.thumbnail_generator import (
    IThumbnailGenerator,
)
from util.flet import file_picker_row

logger = getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.DEBUG)

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


def run_shell_script(callback: Callable[[str], None]) -> None:
    """
    シェルスクリプトを実行する。

    Args:
        callback: 実行状況を通知するためのログ出力関数。
    """
    if hasattr(sys, "_MEIPASS"):
        script_path = os.path.join(sys._MEIPASS, "script/install.sh")
    else:
        script_path = os.path.join(os.getcwd(), "script/install.sh")

    try:
        callback("シェルスクリプトを実行しています...")
        subprocess.check_call(["bash", script_path])
        callback("シェルスクリプトの実行が完了しました。")
    except subprocess.CalledProcessError as e:
        callback(f"エラー: スクリプト実行中に問題が発生しました: {e}")
        sys.exit(1)


def is_wheel_installed(wheel_path: str, callback: Callable[[str], None]) -> bool:
    """
    Wheelファイルがすでにインストールされているか確認する。

    Args:
        wheel_path: 確認対象のWheelファイルのパス。
        callback: 実行状況を通知するためのログ出力関数。

    Returns:
        bool: インストール済みの場合はTrue、未インストールの場合はFalse。
    """
    try:
        # Wheelファイルの名前からパッケージ名を推定
        package_name = os.path.basename(wheel_path).split("-")[0]
        # pip showでパッケージの情報を取得
        subprocess.check_output(
            [sys.executable, "-m", "pip", "show", package_name],
            stderr=subprocess.DEVNULL,
        )
        callback(f"Wheelファイル {package_name} はすでにインストールされています。")
        return True
    except subprocess.CalledProcessError:
        return False


def install_wheel(callback: Callable[[str], None]) -> None:
    """
    ダウンロードしたwheelファイルをPython環境にインストールする。

    Args:
        callback: 実行状況を通知するためのログ出力関数。
    """
    if hasattr(sys, "_MEIPASS"):
        wheel_dir = os.path.join(sys._MEIPASS, "lib")
    else:
        wheel_dir = os.path.join(os.getcwd(), "lib")

    try:
        for filename in os.listdir(wheel_dir):
            if filename.endswith(".whl"):
                wheel_path: str = os.path.join(wheel_dir, filename)
                if is_wheel_installed(wheel_path, callback):
                    continue  # すでにインストールされている場合はスキップ

                callback(f"インストール中: {wheel_path}")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--verbose", wheel_path]
                )
                callback(f"インストール完了: {wheel_path}")
    except Exception as e:
        callback(f"エラー: Wheelインストール中に問題が発生しました: {e}")
        sys.exit(1)


def main(page: ft.Page) -> None:
    page.title = "Shoooorter"
    page.scroll = "adaptive"

    # ログ出力用
    log_output: ft.Text = ft.Text(
        value="セットアップを開始します...", size=14, selectable=True
    )
    page.add(log_output)

    def append_log(message: str) -> None:
        """
        ログメッセージをUIに追加する。

        Args:
            message: 追加するログメッセージ。
        """
        log_output.value += f"\n{message}"
        page.update()

    def setup() -> None:
        """
        セットアップ処理を実行する。
        """
        # シェルスクリプト実行
        run_shell_script(append_log)
        # Wheelインストール
        install_wheel(append_log)
        append_log("セットアップが完了しました！")

    def on_start(e: ft.ControlEvent) -> None:
        """
        セットアップ開始ボタンがクリックされたときのイベントハンドラ。

        Args:
            e: ボタンのクリックイベント。
        """
        append_log("セットアップを開始しています...")
        threading.Thread(target=setup).start()

    # ボタンでセットアップ開始
    start_button: ft.ElevatedButton = ft.ElevatedButton(
        text="セットアップを開始", on_click=on_start
    )
    page.add(start_button)

    page.add(app(page))


def app(page: ft.Page) -> ft.Stack:
    # 入力フォームの構成
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
        onnxruntime_lib_path=get_onnxruntime_lib_path(),
        open_jtalk_dict_dir_path=get_open_jtalk_dict_dir_path(),
        font_path_select=font_path_select,
        output_dir_item=output_dir_item,
    )

    environment_check_button = environment_check_dialog(
        page,
    )
    others_column = ft.Column(
        [
            ft.Text("その他設定", size=24, weight="bold"),
            environment_check_button,
        ],
        spacing=10,
        scroll="adaptive",
    )

    return ft.Column(
        [
            common_setting_column,
            ft.Divider(),
            bulletin_setting_column,
            ft.Divider(),
            others_column,
        ],
        spacing=10,
        scroll="adaptive",
        expand=True,
    )


def bulletin_setting(
    page: ft.Page,
    openai_api_key_input: ft.TextField,
    onnxruntime_lib_path: str,
    open_jtalk_dict_dir_path: str,
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


def get_onnxruntime_lib_path() -> str:
    for path in os.listdir(LIB_PATH):
        if path.startswith("onnxruntime"):
            full_path = os.path.join(LIB_PATH, path, "lib", "libonnxruntime.dylib")
            if os.path.isfile(full_path):
                return full_path
    raise FileNotFoundError("ONNX Runtimeのライブラリが見つかりませんでした。")


def get_open_jtalk_dict_dir_path() -> str:
    for path in os.listdir(LIB_PATH):
        if path.startswith("open_jtalk_dic_utf_8"):
            return os.path.join(LIB_PATH, path)
    raise FileNotFoundError("Open JTalkの辞書ディレクトリが見つかりませんでした。")


def environment_check_dialog(
    page: ft.Page,
) -> ft.ElevatedButton:
    def is_voicevox_core_exist() -> bool:
        for path in os.listdir(LIB_PATH):
            if path.startswith("voicevox_core") and path.endswith(".whl"):
                return True
        return False

    def is_onnxruntime_exist() -> bool:
        for path in os.listdir(LIB_PATH):
            if path.startswith("onnxruntime"):
                full_path = os.path.join(LIB_PATH, path, "lib", "libonnxruntime.dylib")
                if os.path.isfile(full_path):
                    return True
        return False

    def is_openjtalk_exist() -> bool:
        for path in os.listdir(LIB_PATH):
            if path.startswith("open_jtalk_dic_utf_8"):
                return True

        return False

    content = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("VOICEVOX Coreのインストール状況: "),
                    ft.Text(
                        f"{'OK' if is_voicevox_core_exist() else 'NG'}",
                        color="green" if is_voicevox_core_exist() else "red",
                    ),
                ],
                alignment="spaceBetween",
            ),
            ft.Row(
                [
                    ft.Text("ONNX Runtimeのインストール状況: "),
                    ft.Text(
                        f"{'OK' if is_onnxruntime_exist() else 'NG'}",
                        color="green" if is_onnxruntime_exist() else "red",
                    ),
                ],
                alignment="spaceBetween",
            ),
            ft.Row(
                [
                    ft.Text("Open JTalkのインストール状況: "),
                    ft.Text(
                        f"{'OK' if is_openjtalk_exist() else 'NG'}",
                        color="green" if is_openjtalk_exist() else "red",
                    ),
                ],
                alignment="spaceBetween",
            ),
        ]
    )

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("環境チェック"),
        content=content,
        actions=[ft.ElevatedButton("閉じる", on_click=lambda e: handle_close(e))],
        actions_alignment="end",
    )

    button = ft.ElevatedButton(
        text="環境チェック",
        on_click=lambda e: page.open(dialog),
    )

    def handle_close(e: ft.ControlEvent) -> None:
        page.close(dialog)

    return button


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


if __name__ == "__main__":
    ft.app(target=main)
