import logging
from typing import List

from openai import OpenAI

from .manuscript_generator import IManuscriptGenerator, Manuscript


class TriviaManuscriptGenerator(IManuscriptGenerator):
    def __init__(
        self,
        themes: List[str],
        num_trivia: int,
        openai_apikey: str,
        logger: logging.Logger,
    ) -> None:
        super().__init__(logger)
        self.themes = themes
        self.num_trivia = num_trivia
        try:
            self.openai_client = OpenAI(api_key=openai_apikey)
        except ValueError as e:
            raise e

    def generate(self) -> Manuscript:
        completion = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": f"{','.join(self.themes)}に関する誰も知らないようなトリビアを{self.num_trivia}個生成してください。できる限り信ぴょう性の高いものを検索に基づいて生成してください。",
                },
                {
                    "role": "system",
                    "content": "なお、各トリビアはManuscript.content.textに格納してください。",
                },
                {
                    "role": "system",
                    "content": "また、タイトルは15文字以内としてください。",
                },
                {
                    "role": "system",
                    "content": "また、各トリビアは50文字以内としてください。",
                },
                {
                    "role": "system",
                    "content": "また、各トリビアは個人や会社などの特定の団体を中傷する内容や嘘を含んではいけません。",
                },
            ],
            response_format=Manuscript,
        )

        manuscript = completion.choices[0].message.parsed
        if not manuscript:
            raise Exception("GPT-4oによる文章生成に失敗しました。")

        self.logger.debug(manuscript)

        self.logger.info("GPTによるトリビアに基づいた原稿を生成しました")

        return manuscript
