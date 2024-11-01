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

    def character_image_paths(self) -> List[str]:
        return self.character_image_file_paths

    def random_character_image_path(self) -> str:
        return random.choice(self.character_image_file_paths)

    def background_image_paths(self) -> List[str]:
        return self.background_file_paths

    def random_background_image_path(self) -> str:
        return random.choice(self.background_file_paths)
