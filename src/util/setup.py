import logging
import os
import platform
import shutil
import subprocess
import sys
import urllib
import urllib.request
from pathlib import Path
from typing import Literal

VOICEVOX_VERSION = "0.15.4"


def detect_os() -> Literal["macos", "linux", "windows"]:
    os_name = platform.system()
    if os_name == "Darwin":
        return "macos"
    elif os_name == "Linux":
        return "linux"
    elif os_name in {"Windows", "CYGWIN", "MINGW"}:
        return "windows"
    else:
        raise NotImplementedError(f"{os_name}はサポートされていないOSです")


def detect_arch() -> Literal["x86_64", "arm64", "x86"]:
    arch = platform.machine()
    if arch in {"x86_64", "AMD64"}:
        return "x86_64"
    elif arch in {"arm64", "aarch64"}:
        return "arm64"
    elif arch in {"i386", "i686"}:
        return "x86"
    else:
        raise NotImplementedError(f"{arch}はサポートされていないアーキテクチャです")


def detect_device() -> Literal["cpu", "cuda", "directml"]:
    if platform.system() == "Linux" and shutil.which("nvidia-smi"):
        return "cuda"
    elif platform.system() == "Windows":
        if shutil.which("dmlinfo"):
            return "directml"
        else:
            return "cpu"
    else:
        return "cpu"


def voicevox_wheel_name(
    os_name: Literal["macos", "linux", "windows"],
    arch: Literal["x86_64", "arm64", "x86"],
    device: Literal["cpu", "cuda", "directml"],
) -> str:
    mapping = {
        "windows-x86_64-cpu": f"voicevox_core-{VOICEVOX_VERSION}+cpu-cp38-abi3-win_amd64.whl",
        "windows-x86_64-directml": f"voicevox_core-{VOICEVOX_VERSION}+directml-cp38-abi3-win_amd64.whl",
        "windows-x86_64-cuda": f"voicevox_core-{VOICEVOX_VERSION}+cuda-cp38-abi3-win_amd64.whl",
        "windows-x86-cpu": f"voicevox_core-{VOICEVOX_VERSION}+cpu-cp38-abi3-win32.whl",
        "macos-x86_64-cpu": f"voicevox_core-{VOICEVOX_VERSION}+cpu-cp38-abi3-macosx_10_7_x86_64.whl",
        "macos-arm64-cpu": f"voicevox_core-{VOICEVOX_VERSION}+cpu-cp38-abi3-macosx_11_0_arm64.whl",
        "linux-x86_64-cpu": f"voicevox_core-{VOICEVOX_VERSION}+cpu-cp38-abi3-linux_x86_64.whl",
        "linux-aarch64-cpu": f"voicevox_core-{VOICEVOX_VERSION}+cpu-cp38-abi3-linux_aarch64.whl",
        "linux-x86_64-cuda": f"voicevox_core-{VOICEVOX_VERSION}+cuda-cp38-abi3-linux_x86_64.whl",
    }
    key = f"{os_name}-{arch}-{device}"
    if key in mapping:
        return mapping[key]
    else:
        raise NotImplementedError(
            f"{key}はサポートされていないOS/アーキテクチャ/デバイスの組み合わせです"
        )


def voicevox_wheel_url(
    os_name: Literal["macos", "linux", "windows"],
    arch: Literal["x86_64", "arm64", "x86"],
    device: Literal["cpu", "cuda", "directml"],
) -> str:
    filename = voicevox_wheel_name(os_name, arch, device)
    return f"https://github.com/VOICEVOX/voicevox_core/releases/download/{VOICEVOX_VERSION}/{filename}"


def check_is_installed_voicevox_wheel() -> bool:
    try:
        subprocess.check_output(
            [sys.executable, "-m", "pip", "show", "voicevox_core"],
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def download_and_install_voicevox_wheel(
    logger: logging.Logger,
    output_dir: str,
) -> None:
    os_name = detect_os()
    arch = detect_arch()
    device = detect_device()

    url = voicevox_wheel_url(os_name, arch, device)
    output_path = Path(output_dir) / Path(url).name

    logger.info("VOICEVOXのPython wheelをダウンロード状況を確認します...")
    if output_path.exists():
        logger.info("VOICEVOXのPython wheelは既にダウンロードされています。")
    else:
        logger.info(
            f"VOICEVOXのPython wheelをダウンロードし、${output_dir}に保存します..."
        )
        urllib.request.urlretrieve(url, output_path)
        logger.info("VOICEVOXのPython wheelのダウンロードが完了しました。")

    logger.info("VOICEVOXのPython wheelのインストール状況を確認します...")
    try:
        package_name = os.path.basename(output_path).split("-")[0]
        subprocess.check_output(
            [sys.executable, "-m", "pip", "show", package_name],
            stderr=subprocess.DEVNULL,
        )
        logger.info("VOICEVOXのPython wheelは既にインストールされています。")
        return
    except subprocess.CalledProcessError:
        pass
    logger.info("VOICEVOXのPython wheelをインストールします...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--verbose", str(output_path)],
    )
    logger.info("VOICEVOXのPython wheelのインストールが完了しました。")


def check_is_downloaded_voicevox_dependencies(
    output_dir: str,
) -> bool:
    output_dir = os.path.join(output_dir, "voicevox_core")
    if not os.path.exists(output_dir):
        return False
    onnx_files_exist = any(
        f.startswith("libonnxruntime") for f in os.listdir(output_dir)
    )
    open_jtalk_files_exist = any(
        f.startswith("open_jtalk_dic_utf_8") for f in os.listdir(output_dir)
    )
    return onnx_files_exist and open_jtalk_files_exist


def check_is_installed_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def download_voicevox_dependencies(
    logger: logging.Logger,
    output_dir: str,
) -> None:
    onnx_files_exist = any(f.startswith("onnxruntime") for f in os.listdir(output_dir))
    open_jtalk_files_exist = any(
        f.startswith("open_jtalk_dic_utf_8") for f in os.listdir(output_dir)
    )

    logger.info("VOICEVOXの依存関係のダウンロード状況を確認します...")
    if onnx_files_exist and open_jtalk_files_exist:
        logger.info(
            "onnxruntimeおよびopen_jtalk_dic_utf_8の依存関係は既にダウンロードされています。"
        )
        return

    logger.info(f"VOICEVOXの依存関係をダウンロードし、{output_dir}に保存します...")
    subprocess.run(
        [
            "bash",
            "-c",
            "curl -sSfL https://github.com/VOICEVOX/voicevox_core/releases/latest/download/download.sh | bash -s",
        ],
        cwd=output_dir,
        check=True,
    )
    logger.info("VOICEVOXの依存関係のダウンロードが完了しました。")


def get_onnxruntime_lib_path(
    output_dir: str,
) -> str:
    output_dir = os.path.join(output_dir, "voicevox_core")
    for path in os.listdir(output_dir):
        if path.startswith("libonnxruntime"):
            full_path = os.path.join(output_dir, path)
            return full_path
    raise FileNotFoundError("ONNX Runtimeのライブラリが見つかりませんでした。")


def get_open_jtalk_dict_dir_path(
    output_dir: str,
) -> str:
    output_dir = os.path.join(output_dir, "voicevox_core")
    for path in os.listdir(output_dir):
        if path.startswith("open_jtalk_dic_utf_8"):
            return os.path.join(output_dir, path)
    raise FileNotFoundError("Open JTalkの辞書ディレクトリが見つかりませんでした。")
