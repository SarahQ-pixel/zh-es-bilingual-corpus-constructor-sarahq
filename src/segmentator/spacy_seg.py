import yaml
import spacy


_NLP_CACHE = None


def load_config():
    with open("config/segmentator_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_nlp(language):
    global _NLP_CACHE

    if _NLP_CACHE is None:
        _NLP_CACHE = {}

    if language not in _NLP_CACHE:
        config = load_config()
        model_name = config["spacy_seg"]["models"][language]
        _NLP_CACHE[language] = spacy.load(model_name)

    return _NLP_CACHE[language]


def ensure_sentence_end(text, sentence_config):
    text = text.strip()

    if text == "":
        return ""

    sentence_endings = tuple(sentence_config["valid"])

    if text.endswith(sentence_endings):
        return text

    return text + sentence_config["default"]


def merge_texts(language, texts, threshold, sentence_config):
    merged_texts = []

    buffer = []
    buffer_length = 0

    for text in texts:
        normalized_text = ensure_sentence_end(
            text = text, 
            sentence_config=sentence_config)

        if normalized_text == "":
            continue
        buffer.append(normalized_text)
        buffer_length += len(normalized_text)
        if buffer_length >= threshold:
            merged_texts.append(" ".join(buffer))
            buffer = []
            buffer_length = 0

    if buffer:
        merged_texts.append(" ".join(buffer))

    return merged_texts


def sapacy_seg(language, texts: list[str]):
    config = load_config()

    sentence_config = config["spacy_seg"]["sentence_endings"][language]
    threshold = config["spacy_seg"]["merge_text_length_threshold"]

    merged_texts = merge_texts(
        language = language,
        texts = texts,
        threshold = threshold,
        sentence_config=sentence_config
    )

    nlp = get_nlp(language)
    sentences = []

    for merged_text in merged_texts:
        doc = nlp(merged_text)
        for sentence in doc.sents:
            sentence_text = sentence.text.strip()
            if sentence_text:
                sentences.append(sentence_text)

    return sentences