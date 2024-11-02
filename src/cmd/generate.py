import logging
import os
import sys
from logging import getLogger

import typer
import ulid
from dotenv import load_dotenv

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from module.audio_generator import IAudioGenerator  # noqa: E402
from module.audio_generator.voicevox_audio_generator import (  # noqa: E402
    VoiceVoxAudioGenerator,
)
from module.manuscript_generator import (  # noqa: E402
    BulletinBoardManuscriptGenerator,
    IManuscriptGenerator,
    PseudoBulletinBoardManuscriptGenerator,
    TriviaManuscriptGenerator,
)
from module.movie_generator import (  # noqa: E402
    DalleShortMovieGenerator,
    IMovieGenerator,
    IrasutoyaLongMovieGenerator,
    IrasutoyaShortMovieGenerator,
)
from module.thumbnail_generator import (  # noqa: E402
    BulletinBoardLongThumbnailGenerator,
    DalleThumbnailGenerator,
    IThumbnailGenerator,
)

logger = getLogger(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = typer.Typer()


@app.command()
def bulletin(
    url: str = typer.Argument(..., help="掲示板URL"),
    short: bool = typer.Option(False, help="短尺動画を生成するかどうか"),
    resume_step: str = typer.Option(None, help="どのステップから再開するか"),
    resume_id: str = typer.Option(None, help="どのIDを再開するか"),
    debug: bool = typer.Option(False, help="Debugモード"),
) -> None:
    set_log_level(debug)
    movie_id = get_id(resume_id)

    logger.info(f"掲示板から{'短尺' if short else '長尺'}動画を生成します")
    logger.info(f"参照URL: {url}")

    manuscript_generator = BulletinBoardManuscriptGenerator(
        id=movie_id,
        source_url=url,
        openai_apikey=OPENAI_API_KEY,
        logger=logger,
    )

    audio_generator = VoiceVoxAudioGenerator(id=movie_id, logger=logger)

    if not short:
        thumbnail_generator = BulletinBoardLongThumbnailGenerator(
            id=movie_id, logger=logger
        )
    else:
        thumbnail_generator = DalleThumbnailGenerator(
            id=movie_id, openai_apikey=OPENAI_API_KEY, is_short=short, logger=logger
        )

    if not short:
        movie_generator = IrasutoyaLongMovieGenerator(id=movie_id, logger=logger)
    else:
        movie_generator = IrasutoyaShortMovieGenerator(id=movie_id, logger=logger)

    pipeline(
        manuscript_generator,
        audio_generator,
        thumbnail_generator,
        movie_generator,
        movie_id,
        resume_step,
    )


@app.command()
def pseudo_bulletin(
    themes: str = typer.Argument(
        ..., help="生成したい掲示板のテーマをコンマ区切りで指定"
    ),
    short: bool = typer.Option(False, help="短尺動画を生成するかどうか"),
    resume_step: str = typer.Option(None, help="どのステップから再開するか"),
    resume_id: str = typer.Option(None, help="どのIDを再開するか"),
    debug: bool = typer.Option(False, help="Debugモード"),
) -> None:
    set_log_level(debug)
    movie_id = get_id(resume_id)

    logger.info(
        f"GPTを用いた疑似掲示板から{'短尺' if short else '長尺'}動画を生成します"
    )
    logger.info(f"テーマ: {themes}")

    manuscript_generator = PseudoBulletinBoardManuscriptGenerator(
        id=movie_id,
        themes=themes.split(","),
        openai_apikey=OPENAI_API_KEY,
        logger=logger,
    )

    audio_generator = VoiceVoxAudioGenerator(id=movie_id, logger=logger)

    if not short:
        thumbnail_generator = BulletinBoardLongThumbnailGenerator(
            id=movie_id, logger=logger
        )
    else:
        thumbnail_generator = DalleThumbnailGenerator(
            id=movie_id, openai_apikey=OPENAI_API_KEY, is_short=short, logger=logger
        )

    if not short:
        movie_generator = IrasutoyaLongMovieGenerator(id=movie_id, logger=logger)
    else:
        movie_generator = IrasutoyaShortMovieGenerator(id=movie_id, logger=logger)

    pipeline(
        manuscript_generator,
        audio_generator,
        thumbnail_generator,
        movie_generator,
        movie_id,
        resume_step,
    )


@app.command()
def trivia(
    themes: str = typer.Argument(..., help="Triviaのテーマをコンマ区切りで指定"),
    num_trivia: int = typer.Option(5, help="Triviaの数(デフォルト: 5)"),
    short: bool = typer.Option(False, help="短尺動画を生成するかどうか"),
    voicevox_speaker_id: int = typer.Option(3, help="VoiceVoxの話者ID(デフォルト: 3)"),
    resume_step: str = typer.Option(None, help="どのステップから再開するか"),
    resume_id: str = typer.Option(None, help="どのIDを再開するか"),
    debug: bool = typer.Option(False, help="Debugモード"),
) -> None:
    set_log_level(debug)
    movie_id = get_id(resume_id)

    logger.info(
        f"GPTを用いて生成したトリビアから{'短尺' if short else '長尺'}動画を生成します"
    )
    logger.info(f"テーマ: {themes}")

    manuscript_generator = TriviaManuscriptGenerator(
        id=movie_id,
        themes=themes.split(","),
        num_trivia=num_trivia,
        openai_apikey=OPENAI_API_KEY,
        logger=logger,
    )

    audio_generator = VoiceVoxAudioGenerator(
        id=movie_id,
        logger=logger,
        content_speaker_id=voicevox_speaker_id,
    )

    thumbnail_generator = DalleThumbnailGenerator(
        id=movie_id,
        openai_apikey=OPENAI_API_KEY,
        is_short=short,
        logger=logger,
    )

    if not short:
        raise NotImplementedError("Triviaの長尺動画は未実装です")
    else:
        movie_generator = DalleShortMovieGenerator(
            id=movie_id, openai_apikey=OPENAI_API_KEY, logger=logger
        )

    pipeline(
        manuscript_generator,
        audio_generator,
        thumbnail_generator,
        movie_generator,
        movie_id,
        resume_step,
    )


def get_id(resume_id: str | None) -> str:
    if resume_id is not None:
        logger.info(f"次のIDを再開します: {resume_id}")
        return resume_id
    else:
        new_id = ulid.new().str
        logger.info(f"新しいID: {new_id}")
        return new_id


def set_log_level(debug: bool) -> None:
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def pipeline(
    manuscript_genetrator: IManuscriptGenerator,
    audio_generator: IAudioGenerator,
    thumbnail_generator: IThumbnailGenerator,
    movie_generator: IMovieGenerator,
    movie_id: str,
    resume_step: str | None = None,
) -> None:
    if not resume_step or resume_step == "manuscript":
        logger.info("Step1: 原稿生成")
        try:
            manuscript = manuscript_genetrator.generate()
        except Exception as e:
            logger.error(f"原稿生成中にエラーが発生しました。 {e}")
            logger.error(
                f"次のオプションで再開できます: --resume-id={movie_id} --resume-step=manuscript"
            )
            raise e
    else:
        logger.info("⏭️ Skip: 原稿生成")
        manuscript = manuscript_genetrator.skip()

    if not resume_step or resume_step == "manuscript" or resume_step == "audio":
        logger.info("Step2: 音声合成")
        try:
            audio = audio_generator.generate(manuscript)
        except Exception as e:
            logger.error(f"音声合成中にエラーが発生しました。 {e}")
            logger.error(
                f"次のオプションで再開できます: --resume-id={movie_id} --resume-step=audio"
            )
            raise e
    else:
        logger.info("⏭️ Skip: 音声合成")
        audio = audio_generator.skip()

    if (
        not resume_step
        or resume_step == "manuscript"
        or resume_step == "audio"
        or resume_step == "thumbnail"
    ):
        logger.info("Step3: サムネイル生成")
        try:
            thumbnail_generator.generate(manuscript)
        except Exception as e:
            logger.error(f"サムネイル生成中にエラーが発生しました。 {e}")
            logger.error(
                f"次のオプションで再開できます: --resume-id={movie_id} --resume-step=thumbnail"
            )
            raise e
    else:
        logger.info("⏭️ Skip: サムネイル生成")
        thumbnail_generator.skip()

    if (
        not resume_step
        or resume_step == "manuscript"
        or resume_step == "audio"
        or resume_step == "thumbnail"
        or resume_step == "movie"
    ):
        logger.info("Step4: 動画生成")
        try:
            movie_generator.generate(manuscript, audio)
        except Exception as e:
            logger.error(f"動画生成中にエラーが発生しました。 {e}")
            logger.error(
                f"次のオプションで再開できます: --resume-id={movie_id} --resume-step=movie"
            )
            raise e
    else:
        logger.info("⏭️ Skip: 動画生成")

    logger.info("すべてのステップを正常に終了しました")


if __name__ == "__main__":
    app()
