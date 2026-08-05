from pathlib import Path
import numpy as np
import yaml
import torch
from sentence_transformers import SentenceTransformer


_MODEL_CACHE = {}


def load_config():
    with open("config/sentence_align_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_device(config):
    device = config["sentence_emb"]["device"]
    if device == "auto":
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    
    return device


def load_model(model_name, device):
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = SentenceTransformer(
            model_name,
            device=device
        )

    return _MODEL_CACHE[model_name]


def encode(sentences,show_progress_bar=False):
    if len(sentences) == 0:
        return np.array([], dtype=np.float32)

    config = load_config()
    device = get_device(config)
    model_name = config["sentence_emb"]["model"]
    model = load_model(model_name, device)
    batch_size = config["sentence_emb"]["batch_size"]

    normalize = config["sentence_emb"]["normalize"]

    embeddings = model.encode(
        sentences,
        batch_size=batch_size,
        show_progress_bar=show_progress_bar,
        normalize_embeddings=normalize
    )

    return np.asarray(
        embeddings,
        dtype=np.float32
    )