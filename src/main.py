import logging
import os
import subprocess
import sys
import threading
from logging import getLogger
from typing import Callable

import flet as ft

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

    page.add(app())


def app() -> ft.Stack:
    openai_apikey_input = ft.TextField(
        label="OpenAI APIキー",
        hint_text="OpenAIのAPIキーを入力してください",
    )
    output_dir_path_input = ft.TextField(
        label="出力先ディレクトリ",
        hint_text="動画の出力先ディレクトリを入力してください",
    )
    onnxruntime_lib_path_input = ft.TextField(
        label="ONNXRUNTIME lib path",
    )
    open_jtalk_dict_dir_path_input = ft.TextField(
        label="OPENJTALK dict dir path",
    )
    font_path_input = ft.TextField(
        label="Font path",
    )
    bulletin_st = bulletin(
        openai_api_key=openai_apikey_input.value,
        output_dir=output_dir_path_input.value,
        onnxruntime_lib_path=onnxruntime_lib_path_input.value,
        open_jtalk_dict_dir_path=open_jtalk_dict_dir_path_input.value,
        font_path=font_path_input.value,
    )
    st = ft.Stack(
        [
            ft.Text(
                "Auto Movie Generator",
                size=40,
                weight="bold",
            ),
            openai_apikey_input,
            output_dir_path_input,
            onnxruntime_lib_path_input,
            open_jtalk_dict_dir_path_input,
            font_path_input,
            bulletin_st,
        ]
    )

    return st


def bulletin(
    openai_api_key: str,
    output_dir: str,
    onnxruntime_lib_path: str,
    open_jtalk_dict_dir_path: str,
    font_path: str,
) -> ft.Stack:
    # TODO: 実際には複数のテーマに対応するが、GUI実装の都合上一つのみ受け入れる
    theme_input = ft.TextField(
        label="テーマ",
        hint_text="議論させたいテーマを入力してください",
    )
    man_image_dir_input = ft.TextField(
        label="男性画像ディレクトリ",
        hint_text="男性画像ディレクトリを入力してください",
    )
    woman_image_dir_input = ft.TextField(
        label="女性画像ディレクトリ",
        hint_text="女性画像ディレクトリを入力してください",
    )
    bgm_file_path_input = ft.TextField(
        label="BGMファイルパス",
        hint_text="BGMファイルパスを入力してください",
    )
    bgv_file_path_input = ft.TextField(
        label="BGMファイルパス", hint_text="BGMファイルパスを入力してください"
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

    action_button = ft.ElevatedButton(
        text="動画生成",
        on_click=generate_video,
    )

    st = ft.Stack(
        [
            ft.Text(
                "掲示板風動画生成",
                size=30,
                weight="bold",
            ),
            theme_input,
            action_button,
        ],
        width=300,
        height=300,
    )

    return st


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
