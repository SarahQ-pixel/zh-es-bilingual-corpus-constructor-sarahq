from pathlib import Path
import json
import yaml


def load_config():
    with open("config/corpus_biuld_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(json_path):
    json_path = Path(json_path)

    with open(json_path,"r",encoding="utf-8") as f:
        return json.load(f)


def build_sentence_lookup(json_data):
    sentence_lookup = {}
    zh_lookup = {}

    for item in json_data.get("zh_sentences",[]):
        sentence_id = item.get("sentence_id","")
        zh_lookup[sentence_id] = item.get("text","")

    sentence_lookup["zh"] = zh_lookup

    es_lookup = {}

    for item in json_data.get("es_sentences",[]):
        sentence_id = item.get("sentence_id","")
        es_lookup[sentence_id] = item.get("text","")

    sentence_lookup["es"] = es_lookup

    return sentence_lookup


def load_document(json_path):
    config = load_config()

    future_config_item = config["corpus_biuld_json_1t2"]

    json_data = load_json(json_path)

    return build_sentence_lookup(json_data)


def get_sentence(document,sentence_id,language):
    language_lookup = document.get(language,{})

    if sentence_id not in language_lookup:
        raise KeyError(
            f"Sentence '{sentence_id}' "
            f"not found in language '{language}'."
        )

    return language_lookup[sentence_id]