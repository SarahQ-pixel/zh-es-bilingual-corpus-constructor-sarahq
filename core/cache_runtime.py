import os

def apply_cache_env(layout: dict):
    os.environ["HF_HOME"] = str(layout["hf"])
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(layout["hf"] / "hub")
    os.environ["HF_HUB_CACHE"] = str(layout["hf"] / "hub")

    os.environ["TRANSFORMERS_CACHE"] = str(layout["transformers"])
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(layout["sentence_transformers"])

    os.environ["TORCH_HOME"] = str(layout["torch"])

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(layout["playwright"])

    os.environ["SCRAPY_CACHE_DIR"] = str(layout["scrapy"])

    os.environ["XDG_CACHE_HOME"] = str(layout["root"])

    os.environ["NLTK_DATA"] = str(layout["nltk"])