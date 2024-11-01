import json
import logging
import os


class UploadManager:
    def __init__(self, logger: logging.Logger):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.json_file_path = os.path.join(root_dir, "upload_manager.json")
        self.logger = logger

    def register(self, id: str) -> None:
        if not os.path.exists(self.json_file_path):
            with open(self.json_file_path, "w") as f:
                json.dump({"manager": {}}, f, indent=4)
        with open(self.json_file_path, "r") as f:
            json_data = json.load(f)
        if not json_data["manager"]:
            json_data["manager"] = {}
        if id in json_data["manager"]:
            self.logger.warning(f"ID {id} is already registered.")
            return
        json_data["manager"][id] = {
            "description_template_file_path": "",
            "client_secrets_file_path": "",
        }
        with open(self.json_file_path, "w") as f:
            json.dump(json_data, f, indent=4)

    def remove(self, id: str) -> None:
        with open(self.json_file_path, "r") as f:
            json_data = json.load(f)
        if not json_data["manager"]:
            json_data["manager"] = {}
        if id not in json_data["manager"]:
            self.logger.warning(f"ID {id} is not registered.")
            return
        del json_data["manager"][id]
        with open(self.json_file_path, "w") as f:
            json.dump(json_data, f, indent=4)

    def get_all_ready_ids(self) -> list:
        with open(self.json_file_path, "r") as f:
            json_data = json.load(f)
        if not json_data["manager"]:
            json_data["manager"] = {}
        return [
            id
            for id, data in json_data["manager"].items()
            if data["description_template_file_path"]
            and data["client_secrets_file_path"]
        ]

    def get_client_secrets_file_path(self, id: str) -> str:
        with open(self.json_file_path, "r") as f:
            json_data = json.load(f)
        if not json_data["manager"]:
            json_data["manager"] = {}
        if id not in json_data["manager"]:
            self.logger.warning(f"ID {id} is not registered.")
            return ""
        return json_data["manager"][id]["client_secrets_file_path"]

    def get_description_template_file_path(self, id: str) -> str:
        with open(self.json_file_path, "r") as f:
            json_data = json.load(f)
        if not json_data["manager"]:
            json_data["manager"] = {}
        if id not in json_data["manager"]:
            self.logger.warning(f"ID {id} is not registered.")
            return ""
        return json_data["manager"][id]["description_template_file_path"]
