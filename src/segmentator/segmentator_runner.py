import core.bootstrap
import json
import yaml
from pathlib import Path

from src.segmentator.spacy_seg import sapacy_seg


def load_config():
    with open("config/segmentator_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(json_path: Path):
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(json_path: Path, data):
    json_path.parent.mkdir(parents=True, exist_ok=True)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def load_page_text(page_json_path: Path):
    page_json = load_json(page_json_path)
    texts = page_json.get("text", [])

    if texts is None:
        texts = []

    return {
        "doc_id": page_json["doc_id"],
        "page_path": str(page_json_path),
        "language": page_json["language"],
        "texts": texts,
    }


def build_output_filename(pair_id: str, config):
    prefix = config["output"]["output_filename_prefix"]
    return f"{prefix}{pair_id}.json"


def build_sentence_list(sentence_texts, sentence_prefix):
    sentence_list = []

    for index, sentence in enumerate(sentence_texts, start=1):
        sentence_list.append(
            {
                "sentence_id": f"{sentence_prefix}{index:08d}",
                "text": sentence,
            }
        )

    return sentence_list


def process_pair(pair_json_path: Path, config):
    pair_json = load_json(pair_json_path)

    zh_page = load_page_text(Path(pair_json["zh_page_path"]))
    es_page = load_page_text(Path(pair_json["es_page_path"]))

    zh_sentence_texts = sapacy_seg(
        language=zh_page["language"],
        texts=zh_page["texts"]
    )

    es_sentence_texts = sapacy_seg(
        language=es_page["language"],
        texts=es_page["texts"]
    )

    zh_sentence_prefix = config["spacy_seg"]["sentence_id_prefix"][
        zh_page["language"]
    ]

    es_sentence_prefix = config["spacy_seg"]["sentence_id_prefix"][
        es_page["language"]
    ]

    output_json = {
        "pair_id": pair_json["pair_id"],
        "pair_path": str(pair_json_path),

        "zh_doc_id": pair_json["zh_doc_id"],
        "zh_page_path": pair_json["zh_page_path"],
        "zh_page_language": zh_page["language"],

        "es_doc_id": pair_json["es_doc_id"],
        "es_page_path": pair_json["es_page_path"],
        "es_page_language": es_page["language"],

        "zh_sentences": build_sentence_list(
            zh_sentence_texts,
            zh_sentence_prefix
        ),

        "es_sentences": build_sentence_list(
            es_sentence_texts,
            es_sentence_prefix
        ),
    }

    output_dir = Path(
        config["output"]["segmentated_pages_dir"]
    )

    output_filename = build_output_filename(
        pair_json["pair_id"],
        config
    )

    output_path = output_dir / output_filename

    save_json(
        output_path,
        output_json
    )


def segmentator_runner():
    config = load_config()

    input_dir = Path(
        config["input"]["align_pages_dir"]
    )

    output_dir = Path(
        config["output"]["segmentated_pages_dir"]
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    pair_json_paths = sorted(
        input_dir.glob("*.json")
    )

    for pair_json_path in pair_json_paths:
        process_pair(
            pair_json_path=pair_json_path,
            config=config
        )


if __name__ == "__main__":
    segmentator_runner()