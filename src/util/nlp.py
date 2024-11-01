import fugashi


def tokenize(text: str) -> list[str]:
    tagger = fugashi.Tagger()
    texts = []
    for token in tagger(text):
        texts.append(token.surface)
    return texts

def wrap_text(text: str, num_text_per_line: int) -> list[str]:
    wrapped_texts = []
    line = ""
    for token in tokenize(text):
        if len(line) + len(token) >= num_text_per_line:
            wrapped_texts.append(line)
            line = ""
        line += token
    if line:
        wrapped_texts.append(line)
    return wrapped_texts