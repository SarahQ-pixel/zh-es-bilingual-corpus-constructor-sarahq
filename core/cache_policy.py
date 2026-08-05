from pathlib import Path

def build_cache_layout(project_root: Path, config: dict):
    cache_root = (project_root / config["cache"]["root"]).resolve()

    return {
        "root": cache_root,

        "hf": cache_root / config["cache"]["hf"],
        "transformers": cache_root / config["cache"]["transformers"],
        "sentence_transformers": cache_root / config["cache"]["sentence_transformers"],

        "torch": cache_root / config["cache"]["torch"],
        "playwright": cache_root / config["cache"]["playwright"],
        "scrapy": cache_root / config["cache"]["scrapy"],

        "nltk": cache_root / config["cache"]["nltk"],
    }