import os
import random
from typing import List

current_dir = os.path.dirname(os.path.abspath(__file__))


class ResourceManager:
    def __init__(self) -> None:
        character_image_dir = os.path.join(
            current_dir, "../../material/movie/character"
        )
        self.character_image_file_paths = [
            os.path.join(character_image_dir, f)
            for f in os.listdir(character_image_dir)
            if os.path.isfile(os.path.join(character_image_dir, f)) and f != ".gitkeep"
        ]
        if len(self.character_image_file_paths) == 0:
            raise FileNotFoundError(
                f"次のディレクトリ内にキャラクター画像が見つかりません: {character_image_dir}"
            )
        background_dir = os.path.join(
            current_dir, "../../material/thumbnail/background"
        )
        self.background_file_paths = [
            os.path.join(background_dir, f)
            for f in os.listdir(background_dir)
            if os.path.isfile(os.path.join(background_dir, f)) and f != ".gitkeep"
        ]
        if len(self.background_file_paths) == 0:
            raise FileNotFoundError(
                f"次のディレクトリ内に背景画像が見つかりません: {background_dir}"
            )
        bgm_dir = os.path.join(current_dir, "../../material/movie/bgm")
        self.bgm_file_paths = [
            os.path.join(bgm_dir, f)
            for f in os.listdir(bgm_dir)
            if os.path.isfile(os.path.join(bgm_dir, f)) and f != ".gitkeep"
        ]
        if len(self.bgm_file_paths) == 0:
            raise FileNotFoundError(
                f"次のディレクトリ内にBGMが見つかりません: {bgm_dir}"
            )
        bgv_dir = os.path.join(current_dir, "../../material/movie/bgv")
        self.bgv_file_paths = [
            os.path.join(bgv_dir, f)
            for f in os.listdir(bgv_dir)
            if os.path.isfile(os.path.join(bgv_dir, f)) and f != ".gitkeep"
        ]
        if len(self.bgv_file_paths) == 0:
            raise FileNotFoundError(
                f"次のディレクトリ内に背景動画が見つかりません: {bgv_dir}"
            )
        self.woman_character_image_file_paths = [
            character_image_file_path
            for character_image_file_path in self.character_image_file_paths
            if "_woman_" in character_image_file_path
        ]
        if len(self.woman_character_image_file_paths) == 0:
            raise FileNotFoundError(
                f"次のディレクトリ内に女性の画像が見つかりません。なお、女性画像のファイル名には_woman_を含めてください: {character_image_dir}"
            )
        self.man_character_image_file_paths = [
            character_image_file_path
            for character_image_file_path in self.character_image_file_paths
            if "_man_" in character_image_file_path
        ]
        if len(self.man_character_image_file_paths) == 0:
            raise FileNotFoundError(
                f"次のディレクトリ内に男性の画像が見つかりません。なお、男性画像のファイル名には_man_を含めてください: {character_image_dir}"
            )

    def character_image_paths(self) -> List[str]:
        return self.character_image_file_paths

    def random_character_image_path(self) -> str:
        return random.choice(self.character_image_file_paths)

    def background_image_paths(self) -> List[str]:
        return self.background_file_paths

    def random_background_image_path(self) -> str:
        return random.choice(self.background_file_paths)

    def bgm_paths(self) -> List[str]:
        return self.bgm_file_paths

    def random_bgm_path(self) -> str:
        return random.choice(self.bgm_file_paths)

    def bgv_paths(self) -> List[str]:
        return self.bgv_file_paths

    def random_bgv_path(self) -> str:
        return random.choice(self.bgv_file_paths)

    def man_character_image_paths(self) -> List[str]:
        return self.man_character_image_file_paths

    def random_man_character_image_path(self) -> str:
        return random.choice(self.man_character_image_file_paths)

    def woman_character_image_paths(self) -> List[str]:
        return self.woman_character_image_file_paths

    def random_woman_character_image_path(self) -> str:
        return random.choice(self.woman_character_image_file_paths)
