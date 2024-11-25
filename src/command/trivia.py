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
    TriviaManuscriptGenerator,
)
from module.movie_generator import (  # noqa: E402
    DalleShortMovieGenerator,
    IMovieGenerator,
)
from module.thumbnail_generator import (  # noqa: E402
    DalleThumbnailGenerator,
    IThumbnailGenerator,
)


def trivia_cmd(
    themes: list[str],
    num_trivia: int,
    openai_api_key: str,
    output_dir: str,
    speaker_id: int,
    onnxruntime_lib_path: str,
    open_jtalk_dict_dir_path: str,
    bgm_file_path: str,
    font_path: str,
    logger: Logger,
) -> tuple[
    IManuscriptGenerator,
    IAudioGenerator,
    IThumbnailGenerator,
    IMovieGenerator,
]:
    logger.info("雑学紹介動画を生成します")
    logger.info(f"テーマ: {themes}")

    manuscript_generator = TriviaManuscriptGenerator(
        themes=themes,
        num_trivia=num_trivia,
        openai_apikey=openai_api_key,
        logger=logger,
    )
    audio_generator = VoiceVoxAudioGenerator(
        logger=logger,
        content_speaker_id=speaker_id,
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
    movie_generator = DalleShortMovieGenerator(
        openai_apikey=openai_api_key,
        logger=logger,
        font_path=font_path,
        output_dir=output_dir,
        bgm_file_path=bgm_file_path,
    )

    return manuscript_generator, audio_generator, thumbnail_generator, movie_generator
