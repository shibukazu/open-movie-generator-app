import fugashi


def tokenize(text: str) -> list[str]:
    tagger = fugashi.Tagger()
    texts = []
    for token in tagger(text):
        texts.append(token.surface)
    return texts
