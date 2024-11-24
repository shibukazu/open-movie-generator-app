#!/usr/bin/env bash
set -eu

VOICEVOX_VERSION="0.15.4"
SCRIPT_DIR="$(cd "$(dirname "$0")"; pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.."; pwd)"
OUTPUT_DIR="${ROOT_DIR}/lib"

# OSの判定
detect_os() {
  case "$(uname)" in
    Darwin) echo "macos";;
    Linux) echo "linux";;
    CYGWIN*|MINGW*|MSYS*) echo "windows";;
    *) echo "$(uname)はサポートされていないOSです" >&2; exit 1;;
  esac
}

# CPUアーキテクチャの判定
detect_arch() {
  case "$(uname -m)" in
    x86_64) echo "x86_64";;
    arm64) echo "arm64";;
    aarch64) echo "aarch64";;
    i386|i686) echo "x86";;
    *) echo "$(uname -m)はサポートされていないアーキテクチャです" >&2; exit 1;;
  esac
}

# デバイスの判定
detect_device() {
  if [[ "$(uname)" == "Linux" && -x "$(command -v nvidia-smi)" ]]; then
    echo "cuda"
  elif [[ "$(uname)" =~ "MINGW" || "$(uname)" =~ "CYGWIN" ]]; then
    if [[ -x "$(command -v dmlinfo)" ]]; then
      echo "directml"
    else
      echo "cpu"
    fi
  else
    echo "cpu"
  fi
}

voicevox_wheel_name() {
  os=$1
  arch=$2
  device=$3

  case "$os-$arch-$device" in
    windows-x86_64-cpu) echo "voicevox_core-${VOICEVOX_VERSION}+cpu-cp38-abi3-win_amd64.whl";;
    windows-x86_64-directml) echo "voicevox_core-${VOICEVOX_VERSION}+directml-cp38-abi3-win_amd64.whl";;
    windows-x86_64-cuda) echo "voicevox_core-${VOICEVOX_VERSION}+cuda-cp38-abi3-win_amd64.whl";;
    windows-x86-cpu) echo "voicevox_core-${VOICEVOX_VERSION}+cpu-cp38-abi3-win32.whl";;
    macos-x86_64-cpu) echo "voicevox_core-${VOICEVOX_VERSION}+cpu-cp38-abi3-macosx_10_7_x86_64.whl";;
    macos-arm64-cpu) echo "voicevox_core-${VOICEVOX_VERSION}+cpu-cp38-abi3-macosx_11_0_arm64.whl";;
    linux-x86_64-cpu) echo "voicevox_core-${VOICEVOX_VERSION}+cpu-cp38-abi3-linux_x86_64.whl";;
    linux-aarch64-cpu) echo "voicevox_core-${VOICEVOX_VERSION}+cpu-cp38-abi3-linux_aarch64.whl";;
    linux-x86_64-cuda) echo "voicevox_core-${VOICEVOX_VERSION}+cuda-cp38-abi3-linux_x86_64.whl";;
    *) echo "サポートされていないOS/アーキテクチャ/デバイスの組み合わせです" >&2; exit 1;;
  esac
}

voicevox_wheel_url() {
  filename=$(voicevox_wheel_name "$1" "$2" "$3")
  echo "https://github.com/VOICEVOX/voicevox_core/releases/download/${VOICEVOX_VERSION}/${filename}"
}

# OS, アーキテクチャ, デバイスの情報取得
os=$(detect_os)
arch=$(detect_arch)
device=$(detect_device)

# ダウンロードURLの生成
url=$(voicevox_wheel_url "$os" "$arch" "$device")

# 出力ディレクトリの設定
mkdir -p "$OUTPUT_DIR"
echo "${OUTPUT_DIR}/$(basename "$url")"
# VOICEVOX Python wheelのダウンロード実行
if [[ -e "${OUTPUT_DIR}/$(basename "$url")" ]]; then
  echo "VOICEVOXのPython wheelは既にダウンロードされています。"
else
  echo "VOICEVOXのPython wheelをダウンロードし、${OUTPUT_DIR}に保存します..."
  echo "ダウンロードURL: $url"
  curl -sSL "$url" -o "#!/bin/bash$(basename "$url")"
  echo "VOICEVOXのPython wheelのダウンロードが完了しました。"
fi

# VOICEVOX依存関係のダウンロード実行
if ls "${OUTPUT_DIR}/" | grep -q '^onnxruntime'; then
  if ls "${OUTPUT_DIR}/" | grep -q '^open_jtalk_dic_utf_8'; then
    echo "onnxruntimeおよびopen_jtalk_dic_utf_8の依存関係は既にダウンロードされています。"
    exit 0
  fi
fi

echo "VOICEVOXの依存関係をダウンロードし、${OUTPUT_DIR}に保存します..."
(cd "$OUTPUT_DIR" && curl -sSfL https://github.com/VOICEVOX/voicevox_core/releases/latest/download/download.sh | bash -s)
echo "VOICEVOXの依存関係のダウンロードが完了しました。"
