import core.bootstrap

import json
import hashlib
import yaml
from pathlib import Path

from src.align_page.sequence_matcher import sequence_matcher_sim_cal
from src.align_page.personalized_align import personalized_align_sim_cal
from src.align_page.length_align import length_align_sim_cal
from src.align_page.emb_verif import emb_verif_sim_cal


def load_config():
    with open("config/align_page_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_pages(chunked_dir: Path):
    pages = []

    for chunked_file_path in chunked_dir.glob("*.json"):
        with chunked_file_path.open("r", encoding="utf-8") as f:
            page = json.load(f)
            page["chunked_file_path"] = str(chunked_file_path)
            pages.append(page)

    return pages


def split_by_language(pages, valid_languages):
    filtered = [
        p for p in pages
        if p.get("language") in valid_languages
    ]

    zh_pages = [p for p in filtered if p["language"] == "zh"]
    es_pages = [p for p in filtered if p["language"] == "es"]

    return zh_pages, es_pages


def generate_pair_id(zh_doc_id, es_doc_id):
    raw = f"{zh_doc_id}_{es_doc_id}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def write_pair(output_dir: Path, prefix: str, pair_data: dict):
    pair_id = pair_data["pair_id"]
    chunked_file_path = output_dir / f"{prefix}{pair_id}.json"

    with chunked_file_path.open("w", encoding="utf-8") as f:
        json.dump(pair_data, f, ensure_ascii=False, indent=2)

    return chunked_file_path


def sequence_matcher_runner(zh_pages, es_pages, config, output_dir: Path):

    threshold = config["sequence_matcher"]["sequence_matcher_threshold"]
    prefix = config["output"]["output_file_prefix"]

    candidates = []

    for zh in zh_pages:
        for es in es_pages:
            sim = sequence_matcher_sim_cal(zh, es)
            if sim >= threshold:
                pair_id = generate_pair_id(
                    zh["doc_id"],
                    es["doc_id"]
                )
                pair_obj = {
                    "pair_id": pair_id,
                    "zh_doc_id": zh["doc_id"],
                    "zh_page_path": zh["chunked_file_path"],
                    "es_doc_id": es["doc_id"],
                    "es_page_path": es["chunked_file_path"],

                    "sequence_matcher_similarity": sim,
                    "length_align_similarity": None,
                    "personalized_align_similarity": None,
                    "emb_verif_similarity": None
                }
                write_pair(output_dir, prefix, pair_obj)
                candidates.append(pair_obj)

    return candidates

def length_align_runner(config):
    output_dir = Path(config["output"]["align_pages_dir"])
    threshold = config["length_align"]["length_align_threshold"]

    results = length_align_sim_cal(output_dir)

    for chunked_file_path, score in results:
        chunked_file_path = Path(chunked_file_path)
        if score is None or score < threshold:
            chunked_file_path.unlink()


def personalized_align_runner(config):
    output_dir = Path(config["output"]["align_pages_dir"])
    threshold = config["personalized_align"]["personalized_align_threshold"]

    results = personalized_align_sim_cal(output_dir)

    for chunked_file_path, score in results:
        chunked_file_path = Path(chunked_file_path)
        if score is None or score < threshold:
            chunked_file_path.unlink() 

def emb_verif_runner(config):
    output_dir = Path(config["output"]["align_pages_dir"])
    threshold = config["emb_verif"]["emb_verif_threshold"]

    results = emb_verif_sim_cal(output_dir)

    for chunked_file_path, score in results:
        chunked_file_path = Path(chunked_file_path)
        if score is None or score < threshold:
            chunked_file_path.unlink()

def align_page_runner():
    config = load_config()

    chunked_dir = Path(config["input"]["chunked_pages_dir"])
    output_dir = Path(config["output"]["align_pages_dir"])

    valid_languages = config["align_page_runner"]["valid_languages"]

    output_dir.mkdir(parents=True, exist_ok=True)

    pages = load_pages(chunked_dir)

    zh_pages, es_pages = split_by_language(pages, valid_languages)

    sequence_matcher_runner(
        zh_pages,
        es_pages,
        config,
        output_dir
    )

    length_align_runner(config)

    personalized_align_runner(config)

    emb_verif_runner(config)


if __name__ == "__main__":
    align_page_runner()