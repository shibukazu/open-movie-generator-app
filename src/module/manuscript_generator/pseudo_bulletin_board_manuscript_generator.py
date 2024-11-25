import logging
from typing import List

from openai import OpenAI

from .manuscript_generator import Content, IManuscriptGenerator, Manuscript

EXAMPLE_MANUSCRIPT = Manuscript(
    title="【爆笑】ウブすぎるイッチの美容院初体験",
    overview="今日の動画では、ウブすぎるイッチがみんなに騙されて恥をかいてしまった話を紹介します。",
    keywords=["イッチ", "2ch", "5ch", "まとめ", "創作", "初体験"],
    contents=[
        Content(
            speaker_id="id1",
            text="マイシャンプーいるっていったやつでてこいやwwwww",
            links=[],
        ),
        Content(
            speaker_id="id2",
            text="髪にこだわりがあるやつみたいでいいやん",
            links=[],
        ),
        Content(
            speaker_id="id1",
            text="俺「すいません、マイシャンプー忘れたんですが...」",
            links=[],
        ),
        Content(
            speaker_id="id1",
            text="店員「マイ...シャンプー...?」",
            links=[],
        ),
        Content(
            speaker_id="id3",
            text="ウブすぎてわろた",
            links=[],
        ),
        Content(
            speaker_id="id4",
            text="マイシャンプーってなんやねん",
            links=[],
        ),
        Content(
            speaker_id="id5",
            text="てかお前髪ないやろ",
            links=[],
        ),
        Content(
            speaker_id="id6",
            text="マイリンスも忘れんなよ",
            links=[],
        ),
    ],
)


class PseudoBulletinBoardManuscriptGenerator(IManuscriptGenerator):
    def __init__(
        self, themes: List[str], openai_apikey: str, logger: logging.Logger
    ) -> None:
        super().__init__(logger)
        self.themes = themes
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
                    "content": f"与えられるJSONは一般的な2chの会話風景です。このような形式で{','.join(self.themes)}に関する会話を生成してください。",
                },
                {
                    "role": "system",
                    "content": "なお、会話は必ず30件以上生成してください。30件未満の場合は、会話を続けてください。",
                },
                {
                    "role": "user",
                    "content": EXAMPLE_MANUSCRIPT.json(
                        include={"title", "overview", "keywords", "contents"}
                    ),
                },
            ],
            response_format=Manuscript,
        )

        manuscript = completion.choices[0].message.parsed
        if not manuscript:
            raise Exception("GPT-4oによる文章生成に失敗しました。")
        self.logger.debug(manuscript)

        self.logger.info("GPTによる擬似掲示板に基づいた原稿を生成しました")

        return manuscript
