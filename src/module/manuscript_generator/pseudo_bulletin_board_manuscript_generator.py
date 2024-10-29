import json
import logging
import os
import random

from openai import OpenAI

from .manuscript_generator import IManuscriptGenerator, Manuscript

current_dir = os.path.dirname(os.path.abspath(__file__))


class PseudoBulletinBoardManuscriptGenerator(IManuscriptGenerator):
    def __init__(self, id: str, openai_apikey: str, logger: logging.Logger) -> None:
        super().__init__(id, logger)

        try:
            self.openai_client = OpenAI(api_key=openai_apikey)
        except ValueError as e:
            raise e

    def generate(self) -> Manuscript:
        json_example_manuscript: str
        with open(
            os.path.join(
                current_dir,
                "../../resource/pseudo_bulletin_board/example_manuscript.json",
            ),
            "r",
        ) as f:
            json_example_manuscript = f.read()

        with open(
            os.path.join(
                current_dir, "../../resource/pseudo_bulletin_board/topics.json"
            ),
            "r",
        ) as f:
            json_topics = json.load(f)
        topics = json_topics["topics"]
        themes = list(topics.keys())
        theme = random.choice(themes)
        sub_themes = topics[theme]["sub_themes"]
        sub_theme = random.choice(sub_themes)

        completion = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": f"与えられるJSONは一般的な2chの会話風景です。このような形式で{theme}に関する会話を生成してください。",
                },
                {
                    "role": "system",
                    "content": "なお、会話は必ず70件以上としてください。70件未満の場合は、会話を続けてください。",
                },
                {
                    "role": "system",
                    "content": f"サブテーマは{sub_theme}です。",
                },
                {"role": "user", "content": json_example_manuscript},
            ],
            response_format=Manuscript,
        )

        manuscript = completion.choices[0].message.parsed
        if not manuscript:
            raise Exception("GPT-4oによるクレンジングに失敗しました。")
        manuscript.meta = {
            "type": "pseudo_bulletin_board",
            "theme": theme,
            "sub_theme": sub_theme,
        }
        self.logger.debug(manuscript)

        dump = manuscript.model_dump_json()
        with open(self.dump_file_path, "w") as f:
            f.write(dump)
        return manuscript

        return manuscript
