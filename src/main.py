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

logger = getLogger(__name__)

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
    page.title = "Auto Movie Generator"
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
    output_dir_path_input = ft.TextField(
        label="出力先ディレクトリ",
        hint_text="動画の出力先ディレクトリを入力してください",
        width=400,
    )

    fonts = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
    font_map = {}
    for path in fonts:
        try:
            font_name = font_manager.FontProperties(fname=path).get_name()
            font_map[font_name] = path
        except RuntimeError as e:
            print(f"フォント処理エラー: {path} をスキップします: {e}")
    default_font = next(iter(font_map.keys()), "選択してください")
    font_select = ft.Dropdown(
        label="フォントを選択",
        options=[ft.dropdown.Option(font_name) for font_name in font_map.keys()],
        value=default_font,
        width=400,
    )

    bulletin_st = bulletin(
        page=page,
        openai_api_key=openai_apikey_input.value,
        output_dir=output_dir_path_input.value,
        onnxruntime_lib_path=get_onnxruntime_lib_path(),
        open_jtalk_dict_dir_path=get_open_jtalk_dict_dir_path(),
        font_path=font_map[font_select.value],
    )

    def close_env_check_dialog(e: ft.ControlEvent) -> None:
        page.close(env_check_dialog)

    env_check_dialog = environment_check_dialog(
        page, handle_close=close_env_check_dialog
    )

    environment_check_button = ft.ElevatedButton(
        text="環境チェック",
        on_click=lambda e: page.open(env_check_dialog),
    )

    return ft.Column(
        [
            ft.Text("Auto Movie Generator", size=30, weight="bold"),
            ft.Divider(),
            openai_apikey_input,
            output_dir_path_input,
            font_select,
            ft.Divider(),
            bulletin_st,
            environment_check_button,
        ],
        spacing=10,
        scroll="adaptive",
        expand=True,
    )


def bulletin(
    page: ft.Page,
    openai_api_key: str,
    output_dir: str,
    onnxruntime_lib_path: str,
    open_jtalk_dict_dir_path: str,
    font_path: str,
) -> ft.Stack:
    # フォームの構成
    theme_input = ft.TextField(
        label="テーマ",
        hint_text="議論させたいテーマを入力してください",
        width=400,
    )
    man_image_dir_input = ft.TextField(
        label="男性画像ディレクトリ",
        hint_text="男性画像ディレクトリを入力してください",
        width=400,
    )
    woman_image_dir_input = ft.TextField(
        label="女性画像ディレクトリ",
        hint_text="女性画像ディレクトリを入力してください",
        width=400,
    )
    bgm_file_path_input = ft.TextField(
        label="BGMファイルパス",
        hint_text="BGMファイルパスを入力してください",
        width=400,
    )
    bgv_file_path_input = ft.TextField(
        label="背景動画ファイルパス",
        hint_text="背景動画ファイルパスを入力してください",
        width=400,
    )

    def generate_video(e: ft.ControlEvent) -> None:
        try:
            (
                manuscript_genetrator,
                audio_generator,
                thumbnail_generator,
                movie_generator,
            ) = bulletin_cmd(
                task_id="task_id",
                themes=[theme_input.value],
                openai_api_key=openai_api_key,
                output_dir=output_dir,
                onnxruntime_lib_path=onnxruntime_lib_path,
                open_jtalk_dict_dir_path=open_jtalk_dict_dir_path,
                man_image_dir=man_image_dir_input.value,
                woman_image_dir=woman_image_dir_input.value,
                bgm_file_path=bgm_file_path_input.value,
                bgv_file_path=bgv_file_path_input.value,
                font_path=font_path,
                logger=logger,
            )
            pipeline(
                manuscript_genetrator,
                audio_generator,
                thumbnail_generator,
                movie_generator,
            )
            ft.toast("動画生成が完了しました。")
        except Exception as ex:
            ft.toast(f"エラーが発生しました: {str(ex)}", duration=5000)

    action_button = ft.ElevatedButton(text="動画生成", on_click=generate_video)

    return ft.Column(
        [
            ft.Text("掲示板風動画生成", size=24, weight="bold"),
            ft.Divider(),
            theme_input,
            man_image_dir_input,
            woman_image_dir_input,
            bgm_file_path_input,
            bgv_file_path_input,
            ft.Divider(),
            action_button,
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
    page: ft.Page, handle_close: Callable[[ft.ControlEvent], None]
) -> ft.AlertDialog:
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
    return ft.AlertDialog(
        modal=True,
        title=ft.Text("環境チェック"),
        content=content,
        actions=[ft.ElevatedButton("閉じる", on_click=lambda e: handle_close(e))],
        actions_alignment="end",
    )


def pipeline(
    manuscript_genetrator: IManuscriptGenerator,
    audio_generator: IAudioGenerator,
    thumbnail_generator: IThumbnailGenerator,
    movie_generator: IMovieGenerator,
) -> None:
    logger.info("Step1: 原稿生成")
    try:
        manuscript = manuscript_genetrator.generate()
    except Exception as e:
        logger.error(f"原稿生成中にエラーが発生しました。 {e}")
        raise e

    logger.info("Step2: 音声合成")
    try:
        audio = audio_generator.generate(manuscript)
    except Exception as e:
        logger.error(f"音声合成中にエラーが発生しました。 {e}")
        raise e

    logger.info("Step3: サムネイル生成")
    try:
        thumbnail_generator.generate(manuscript)
    except Exception as e:
        logger.error(f"サムネイル生成中にエラーが発生しました。 {e}")
        raise e

    logger.info("Step4: 動画生成")
    try:
        movie_generator.generate(manuscript, audio)
    except Exception as e:
        logger.error(f"動画生成中にエラーが発生しました。 {e}")
        raise e

    logger.info("すべてのステップを正常に終了しました")


if __name__ == "__main__":
    ft.app(target=main)


def set_log_level(debug: bool) -> None:
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
