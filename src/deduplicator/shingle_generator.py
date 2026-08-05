import json
import yaml
import nltk

from pathlib import Path
from nltk import ngrams
from nltk.data import find
from nltk.tokenize import word_tokenize


def load_config():
    with open("config/deduplicator_config.yaml","r",encoding="utf-8",) as f:
        return yaml.safe_load(f)


def ensure_nltk_resource():

    nltk_cache_path = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "cache"
        / "nltk"
    )

    nltk_cache_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        find(
            "tokenizers/punkt_tab/english/"
        )

    except LookupError:
        nltk.download(
            "punkt_tab",
            download_dir=str(nltk_cache_path),
        )

config = load_config()


ensure_nltk_resource()


def generate_shingles(text):
    if config["shingle_generator"]["lowercase"]:
        text = text.lower()

    tokens = word_tokenize(text)

    shingle_size = config["shingle_generator"]["size"]

    if len(tokens) < shingle_size:
        return [" ".join(tokens)] if tokens else []

    return [
        " ".join(item)
        for item in ngrams(tokens, shingle_size)
    ]


def shingle_generator_runner(id,string,output_path):
    output_path = Path(output_path)

    record = {
        "sentence_id": id,
        "shingles": generate_shingles(string),
        "metadata": {
            "text": string,
        },
    }

    with output_path.open("a",encoding="utf-8") as f:
        json.dump(
            record,
            f,
            ensure_ascii=False,
        )
        f.write("\n")