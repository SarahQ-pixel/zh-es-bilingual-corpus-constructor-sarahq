from pathlib import Path
import json
import yaml


def load_config():
    with open("config/sentence_align_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(json_path):
    json_path = Path(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_sentences(json_data):
    zh_sentences_li = []
    zh_corresp = []

    es_sentences_li = []
    es_corresp = []

    zh_sentences = json_data.get("zh_sentences", [])
    for idx, item in enumerate(zh_sentences):
        text = item.get("text", "")
        sentence_id = item.get("sentence_id", "")
        zh_sentences_li.append(text)
        zh_corresp.append((idx, sentence_id))

    es_sentences = json_data.get("es_sentences", [])
    for idx, item in enumerate(es_sentences):
        text = item.get("text", "")
        sentence_id = item.get("sentence_id", "")
        es_sentences_li.append(text)
        es_corresp.append((idx, sentence_id))

    return zh_sentences_li, zh_corresp, es_sentences_li, es_corresp


def extract_json(json_path):
    config = load_config()
    future_config_item = config["extract_json_1t2"]

    json_data = load_json(json_path)

    return extract_sentences(json_data)