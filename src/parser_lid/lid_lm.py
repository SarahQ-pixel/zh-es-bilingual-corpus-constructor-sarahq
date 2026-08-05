# Language Identification for Web Pages (LID) with Language Model (LM)
import json
import random
from pathlib import Path
import yaml
import langid
from lingua import LanguageDetectorBuilder


def load_config():
    config_path = Path("config/parser_lid_config.yaml")
    with open(config_path,"r",encoding="utf-8") as f:
        return yaml.safe_load(f)


LINGUA_DETECTOR = (
    LanguageDetectorBuilder
    .from_all_languages()
    .build()
)


def detect_with_lingua(text):
    language = (LINGUA_DETECTOR.detect_language_of(text))
    if language is None:
        return "unknown"
    return language.iso_code_639_1.name.lower()


def detect_with_langid(text):
    language, confidence = (
        langid.classify(text)
    )
    return language.lower()


def majority_vote(results):
    counts = {}
    for result in results:
        counts[result] = (counts.get(result,0)+1)
    return max(counts,key=counts.get)


def iden_lm(chunked_page_path):
    config = load_config()

    detector_name = (config["lid_lm"]["detector"])
    sample_size = (config["lid_lm"]["sample_size"])
    random_seed = (config["lid_lm"]["random_seed"])
    
    random.seed(random_seed)

    with open(chunked_page_path,"r",encoding="utf-8") as f:
        page_data = json.load(f)

    text_blocks = page_data.get(
    "text",
    []
    )

    if not text_blocks:
        return
    
    if len(text_blocks) <= sample_size:
        sampled_blocks = text_blocks
    else:
        sampled_blocks = random.sample(
            text_blocks,
            sample_size
        )

    results = []

    for text in sampled_blocks:
        if detector_name == "lingua":
            language = (detect_with_lingua(text))
        elif detector_name == "langid":
            language = (detect_with_langid(text))
        else:
            raise ValueError(
                f"Unsupported detector: "
                f"{detector_name}"
            )
        results.append(language)

    final_language = (majority_vote(results))

    page_data["language"] = (final_language)
    page_data["language_source"] = ("lm")
    page_data["stage_origin"] = ("lm")


    with open(chunked_page_path,"w",encoding="utf-8") as f:
        json.dump(
            page_data,
            f,
            ensure_ascii=False,
            indent=2
        )
