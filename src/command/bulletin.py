import os
import sys
from logging import Logger

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from module.audio_generator.voicevox_audio_generator import (  # noqa: E402
    IAudioGenerator,
    VoiceVoxAudioGenerator,
)
from module.manuscript_generator import (  # noqa: E402
    IManuscriptGenerator,
    PseudoBulletinBoardManuscriptGenerator,
)
from module.movie_generator import (  # noqa: E402
    IMovieGenerator,
    IrasutoyaShortMovieGenerator,
)
from module.thumbnail_generator import (  # noqa: E402
    DalleThumbnailGenerator,
    IThumbnailGenerator,
)


def bulletin_cmd(
    themes: list[str],
    openai_api_key: str,
    output_dir: str,
    onnxruntime_lib_path: str,
    open_jtalk_dict_dir_path: str,
    man_image_dir: str,
    woman_image_dir: str,
    bgm_file_path: str,
    bgv_file_path: str,
    font_path: str,
    logger: Logger,
) -> tuple[
    IManuscriptGenerator,
    IAudioGenerator,
    IThumbnailGenerator,
    IMovieGenerator,
]:
    logger.info("GPTを用いた疑似掲示板から動画を生成します")
    logger.info(f"テーマ: {themes}")

    manuscript_generator = PseudoBulletinBoardManuscriptGenerator(
        themes=themes,
        openai_apikey=openai_api_key,
        logger=logger,
    )
    audio_generator = VoiceVoxAudioGenerator(
        logger=logger,
        output_dir=output_dir,
        onnxruntime_lib_path=onnxruntime_lib_path,
        open_jtalk_dict_dir_path=open_jtalk_dict_dir_path,
    )

    thumbnail_generator = DalleThumbnailGenerator(
        openai_apikey=openai_api_key,
        logger=logger,
        font_path=font_path,
        output_dir=output_dir,
    )
    movie_generator = IrasutoyaShortMovieGenerator(
        logger=logger,
        font_path=font_path,
        output_dir=output_dir,
        man_image_dir=man_image_dir,
        woman_image_dir=woman_image_dir,
        bgm_file_path=bgm_file_path,
        bgv_file_path=bgv_file_path,
    )

    return manuscript_generator, audio_generator, thumbnail_generator, movie_generator
