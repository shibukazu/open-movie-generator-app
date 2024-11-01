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
    IMovieGenerator,
    IrasutoyaMovieGenerator,
    IrasutoyaShortMovieGenerator,
    TriviaShortMovieGenerator,
)
from module.thumbnail_generator import (  # noqa: E402
    BulletinBoardShortThumbnailGenerator,
    BulletinBoardThumbnailGenerator,
    IThumbnailGenerator,
    TriviaShortThumbnailGenerator,
)

logger = getLogger(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = typer.Typer()


@app.command()
def bulletin(
    url: str = typer.Argument(..., help="URL of the bulletin board"),
    thumbnail_generator_type: str = typer.Option(
        "bulletin_board", help="Type of thumbnail generator"
    ),
    movie_generator_type: str = typer.Option(
        "irasutoya", help="Type of movie generator"
    ),
    resume_step: str = typer.Option(None, help="Resume Step"),
    resume_id: str = typer.Option(None, help="Resume ID"),
    debug: bool = typer.Option(False, help="Debug mode"),
) -> None:
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if resume_step is not None:
        if resume_id is None:
            raise ValueError("Resume ID is required")
        else:
            id = resume_id
        logger.info(f"Resume ID: {id}")

        if resume_step == "manuscript":
            logger.info("Resume From Manuscript Generation")
        elif resume_step == "audio":
            logger.info("Resume From Audio Generation")
        elif resume_step == "movie":
            logger.info("Resume From Movie Generation")
        elif resume_step == "thumbnail":
            logger.info("Resume From Thumbnail Generation")
        else:
            raise ValueError(f"Invalid Resume Step: {resume_step}")
    else:
        id = ulid.new().str
        logger.info(f"New ID: {id}")

    logger.info("Generate Movie From Bulletin Board (5ch)")
    logger.info(f"URL: {url}")

    manuscript_generator = BulletinBoardManuscriptGenerator(
        id=id,
        source_url=url,
        openai_apikey=OPENAI_API_KEY,
        logger=logger,
    )

    audio_generator = VoiceVoxAudioGenerator(id=id, logger=logger)

    thumbnail_generator: IThumbnailGenerator = None
    if thumbnail_generator_type == "bulletin_board":
        thumbnail_generator = BulletinBoardThumbnailGenerator(id=id, logger=logger)
    elif thumbnail_generator_type == "bulletin_board_short":
        thumbnail_generator = BulletinBoardShortThumbnailGenerator(id=id, logger=logger)

    movie_generator: IMovieGenerator = None
    if movie_generator_type == "irasutoya":
        movie_generator = IrasutoyaMovieGenerator(id=id, logger=logger)
    elif movie_generator_type == "irasutoya_short":
        movie_generator = IrasutoyaShortMovieGenerator(id=id, logger=logger)
    else:
        raise NotImplementedError(
            f"Movie Generator Type {movie_generator_type} is not implemented"
        )

    pipeline(
        manuscript_generator,
        audio_generator,
        thumbnail_generator,
        movie_generator,
        resume_step,
    )

    typer.echo(id)


@app.command()
def pseudo_bulletin(
    themes: str = typer.Argument(..., help="Themes of the conversation"),
    thumbnail_generator_type: str = typer.Option(
        "bulletin_board", help="Type of thumbnail generator"
    ),
    movie_generator_type: str = typer.Option(
        "irasutoya", help="Type of movie generator"
    ),
    resume_step: str = typer.Option(None, help="Resume Step"),
    resume_id: str = typer.Option(None, help="Resume ID"),
    debug: bool = typer.Option(False, help="Debug mode"),
) -> None:
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if resume_step is not None:
        if resume_id is None:
            raise ValueError("Resume ID is required")
        else:
            id = resume_id
        logger.info(f"Resume ID: {id}")

        if resume_step == "manuscript":
            logger.info("Resume From Manuscript Generation")
        elif resume_step == "audio":
            logger.info("Resume From Audio Generation")
        elif resume_step == "movie":
            logger.info("Resume From Movie Generation")
        elif resume_step == "thumbnail":
            logger.info("Resume From Thumbnail Generation")
        else:
            raise ValueError(f"Invalid Resume Step: {resume_step}")
    else:
        id = ulid.new().str
        logger.info(f"New ID: {id}")

    logger.info("Generate Movie From Pseudo Bulletin Board")

    manuscript_generator = PseudoBulletinBoardManuscriptGenerator(
        id=id,
        themes=themes.split(","),
        openai_apikey=OPENAI_API_KEY,
        logger=logger,
    )

    audio_generator = VoiceVoxAudioGenerator(id=id, logger=logger)

    thumbnail_generator: IThumbnailGenerator = None
    if thumbnail_generator_type == "bulletin_board":
        thumbnail_generator = BulletinBoardThumbnailGenerator(id=id, logger=logger)
    elif thumbnail_generator_type == "bulletin_board_short":
        thumbnail_generator = BulletinBoardShortThumbnailGenerator(id=id, logger=logger)

    movie_generator: IMovieGenerator = None
    if movie_generator_type == "irasutoya":
        movie_generator = IrasutoyaMovieGenerator(id=id, logger=logger)
    elif movie_generator_type == "irasutoya_short":
        movie_generator = IrasutoyaShortMovieGenerator(id=id, logger=logger)
    else:
        raise NotImplementedError(
            f"Movie Generator Type {movie_generator_type} is not implemented"
        )

    pipeline(
        manuscript_generator,
        audio_generator,
        thumbnail_generator,
        movie_generator,
        resume_step,
    )

    typer.echo(id)


@app.command()
def trivia(
    themes: str = typer.Argument(..., help="Themes of the conversation"),
    num_trivia: int = typer.Option(5, help="Number of trivia, Default is 5"),
    voicevox_speaker_id: int = typer.Option(
        3, help="Speaker ID of VoiceVox, Default is Zundamon (3)"
    ),
    resume_step: str = typer.Option(None, help="Resume Step"),
    resume_id: str = typer.Option(None, help="Resume ID"),
    debug: bool = typer.Option(False, help="Debug mode"),
) -> None:
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if resume_step is not None:
        if resume_id is None:
            raise ValueError("Resume ID is required")
        else:
            id = resume_id
        logger.info(f"Resume ID: {id}")

        if resume_step == "manuscript":
            logger.info("Resume From Manuscript Generation")
        elif resume_step == "audio":
            logger.info("Resume From Audio Generation")
        elif resume_step == "movie":
            logger.info("Resume From Movie Generation")
        elif resume_step == "thumbnail":
            logger.info("Resume From Thumbnail Generation")
        else:
            raise ValueError(f"Invalid Resume Step: {resume_step}")
    else:
        id = ulid.new().str
        logger.info(f"New ID: {id}")

    logger.info("Generate Movie From Pseudo Bulletin Board")

    manuscript_generator = TriviaManuscriptGenerator(
        id=id,
        themes=themes.split(","),
        num_trivia=num_trivia,
        openai_apikey=OPENAI_API_KEY,
        logger=logger,
    )

    audio_generator = VoiceVoxAudioGenerator(
        id=id,
        logger=logger,
        content_speaker_id=voicevox_speaker_id,
    )

    thumbnail_generator = TriviaShortThumbnailGenerator(
        id=id,
        openai_apikey=OPENAI_API_KEY,
        logger=logger,
    )

    movie_generator = TriviaShortMovieGenerator(
        id=id, openai_apikey=OPENAI_API_KEY, logger=logger
    )

    pipeline(
        manuscript_generator,
        audio_generator,
        thumbnail_generator,
        movie_generator,
        resume_step,
    )

    typer.echo(id)


def pipeline(
    manuscript_genetrator: IManuscriptGenerator,
    audio_generator: IAudioGenerator,
    thumbnail_generator: IThumbnailGenerator,
    movie_generator: IMovieGenerator,
    resume_step: str | None = None,
) -> None:
    if not resume_step or resume_step == "manuscript":
        logger.info("Step1: Generate Manuscript")
        manuscript = manuscript_genetrator.generate()
    else:
        logger.info("⏭️ Skip: Manuscript Generation")
        manuscript = manuscript_genetrator.skip()

    if not resume_step or resume_step == "manuscript" or resume_step == "audio":
        logger.info("Step2: Generate Audio")
        audio = audio_generator.generate(manuscript)
    else:
        logger.info("⏭️ Skip: Audio Generation")
        audio = audio_generator.skip()

    if (
        not resume_step
        or resume_step == "manuscript"
        or resume_step == "audio"
        or resume_step == "thumbnail"
    ):
        logger.info("Step3: Generate Thumbnail")
        thumbnail_generator.generate(manuscript)
    else:
        logger.info("⏭️ Skip: Thumbnail Generation")
        thumbnail_generator.skip()

    if (
        not resume_step
        or resume_step == "manuscript"
        or resume_step == "audio"
        or resume_step == "thumbnail"
        or resume_step == "movie"
    ):
        logger.info("Step4: Generate Movie")
        movie_generator.generate(manuscript, audio)
    else:
        logger.info("⏭️ Skip: Thumbnail Generation")

    logger.info("All Step Done!")


if __name__ == "__main__":
    app()
