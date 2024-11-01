import logging
import os
import shutil
import sys
from logging import getLogger
from typing import Any

import typer
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from jinja2 import Template

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)


from module.manuscript_generator import Manuscript  # noqa: E402
from util import UploadManager  # noqa: E402

logger = getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()


app = typer.Typer()


@app.command()
def single(
    movie_id: str = typer.Argument(..., help="Movie ID"),
    description_template_file_path: str = typer.Option(
        "", help="Description template file path"
    ),
    client_secrets_file_path: str = typer.Option("", help="Client secrets file path"),
    debug: bool = typer.Option(False, help="Debug mode"),
) -> None:
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    upload_manager = UploadManager(logger=logger)

    logger.info(f"Movie ID: {movie_id}")

    output_dir = os.path.join(current_dir, "../../output", movie_id)
    movie_file_path = os.path.join(output_dir, "movie.mp4")
    thumbnail_file_path = os.path.join(output_dir, "thumbnail.png")
    manuscript_dump_file_path = os.path.join(output_dir, "manuscript.json")
    with open(manuscript_dump_file_path, "r") as f:
        manuscript_dump = f.read()
    manuscript = Manuscript.model_validate_json(manuscript_dump)

    with open(
        description_template_file_path,
    ) as f:
        description_template_file = f.read()
    description_template: Template = Template(source=description_template_file)
    description = description_template.render(
        title=manuscript.title,
        overview=manuscript.overview,
        original_link=manuscript.meta.get("original_link", ""),
    )
    logger.debug(f"Description: {description}")

    def authenticate() -> Any:
        # OAuth2認証のフローを管理
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_file_path,
            ["https://www.googleapis.com/auth/youtube.upload"],
        )
        # ローカルサーバーを使用して認証情報を取得
        credentials = flow.run_local_server(port=0)
        # 認証情報を使用してAPIサービスを構築
        return build("youtube", "v3", credentials=credentials)

    youtube = authenticate()

    request_body = {
        "snippet": {
            "title": manuscript.title,
            "description": description,
            "tags": manuscript.keywords,
            "categoryId": 22,  # blog
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    try:
        logger.info("Uploading movie...")
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=MediaFileUpload(movie_file_path, chunksize=-1, resumable=True),
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
            if "id" in response:
                logger.info(f"Video id '{response['id']}' was successfully uploaded.")
            else:
                logger.info("The upload failed with an unexpected response:", response)

        logger.info("Uploading thumbail...")
        youtube.thumbnails().set(
            videoId=response["id"], media_body=MediaFileUpload(thumbnail_file_path)
        ).execute()
        logger.info(f"Thumbnail id '{response['id']}' was successfully uploaded.")

        # output_dirの中身をすべて削除
        shutil.rmtree(output_dir)
    except HttpError as e:
        logger.error(e)

    upload_manager.remove(movie_id)


@app.command()
def bulk(
    debug: bool = typer.Option(False, help="Debug mode"),
) -> None:
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    upload_manager = UploadManager(logger=logger)
    ready_ids = upload_manager.get_all_ready_ids()
    prev_client_secrets_file_path = None
    if len(ready_ids) == 0:
        logger.info("No movies to upload.")
        return
    for ready_id in ready_ids:
        output_dir = os.path.join(current_dir, "../../output", ready_id)
        movie_file_path = os.path.join(output_dir, "movie.mp4")
        thumbnail_file_path = os.path.join(output_dir, "thumbnail.png")
        manuscript_dump_file_path = os.path.join(output_dir, "manuscript.json")
        with open(manuscript_dump_file_path, "r") as f:
            manuscript_dump = f.read()
        manuscript = Manuscript.model_validate_json(manuscript_dump)

        client_secrets_file_path = upload_manager.get_client_secrets_file_path(ready_id)

        def authenticate() -> Any:
            # OAuth2認証のフローを管理
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file_path,
                ["https://www.googleapis.com/auth/youtube.upload"],
            )
            # ローカルサーバーを使用して認証情報を取得
            credentials = flow.run_local_server(port=0)
            # 認証情報を使用してAPIサービスを構築
            return build("youtube", "v3", credentials=credentials)

        if client_secrets_file_path != prev_client_secrets_file_path:
            youtube = authenticate()
            prev_client_secrets_file_path = client_secrets_file_path

        description_template_file_path = (
            upload_manager.get_description_template_file_path(ready_id)
        )
        with open(
            description_template_file_path,
        ) as f:
            description_template_file = f.read()
        description_template: Template = Template(source=description_template_file)
        description = description_template.render(
            title=manuscript.title,
            overview=manuscript.overview,
            original_title=manuscript.meta.get("thread_title", ""),
        )

        request_body = {
            "snippet": {
                "title": manuscript.title,
                "description": description,
                "tags": manuscript.keywords,
                "categoryId": 22,  # blog
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        try:
            logger.info("Uploading movie...")
            request = youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=MediaFileUpload(
                    movie_file_path, chunksize=-1, resumable=True
                ),
            )
            response = None
            while response is None:
                status, response = request.next_chunk()
                if "id" in response:
                    logger.info(
                        f"Video id '{response['id']}' was successfully uploaded."
                    )
                else:
                    logger.info(
                        "The upload failed with an unexpected response:", response
                    )

            logger.info("Uploading thumbail...")
            youtube.thumbnails().set(
                videoId=response["id"], media_body=MediaFileUpload(thumbnail_file_path)
            ).execute()
            logger.info(f"Thumbnail id '{response['id']}' was successfully uploaded.")

            # output_dirの中身をすべて削除
            shutil.rmtree(output_dir)
        except HttpError as e:
            logger.error(e)

        upload_manager.remove(ready_id)

    logger.info("All movies were successfully uploaded.")


if __name__ == "__main__":
    app()
