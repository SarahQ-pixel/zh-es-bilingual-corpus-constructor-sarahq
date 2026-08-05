import json
import yaml
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.optimize import linear_sum_assignment


def load_config():
    with open("config/align_page_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()


MODEL = SentenceTransformer(
    "paraphrase-multilingual-mpnet-base-v2"
)


def extract_top_texts(page: dict, top_n: int):
    texts = page.get("text", [])
    valid = []

    for item in texts:
        if isinstance(item, str):
            text = item
        elif isinstance(item, dict):
            text = item.get("text", "")
        else:
            continue
        text = text.strip()
        if len(text) == 0:
            continue
        valid.append(
            {
                "text": text,
                "length": len(text)
            }
        )

    valid.sort(
        key=lambda x: x["length"],
        reverse=True
    )

    return valid[:top_n]


def emb_similarity(zh_texts,es_texts):
    if len(zh_texts) == 0 or len(es_texts) == 0:
        return 0.0

    zh_sentences = [
        x["text"]
        for x in zh_texts
    ]

    es_sentences = [
        x["text"]
        for x in es_texts
    ]

    zh_embedding = MODEL.encode(
        zh_sentences,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    es_embedding = MODEL.encode(
        es_sentences,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    cosine_matrix = np.matmul(
        zh_embedding,
        es_embedding.T
    )

    cost_matrix = -cosine_matrix

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    selected_scores = []

    print("Semantic verification pairs:")

    for r, c in zip(row_ind, col_ind):
        score = float(cosine_matrix[r][c])
        selected_scores.append(score)

        print(
            f"ZH Top{r + 1}"
            f" <-> "
            f"ES Top{c + 1}"
            f" | similarity={score:.4f}"
        )
        print(
            f"  ZH: {zh_texts[r]['text'][:120]}"
        )
        print(
            f"  ES: {es_texts[c]['text'][:120]}"
        )
        print("-" * 60)

    if len(selected_scores) == 0:
        return 0.0

    similarity = float(
        np.mean(selected_scores)
    )

    print(
        f"Final emb_verif_similarity = {similarity:.4f}"
    )

    print("=" * 80)

    return similarity


def emb_verif_sim_cal(candidates_dir: Path):
    results = []
    config = load_config()
    top_n = config["emb_verif"]["top_text_num"]

    for file_path in candidates_dir.glob("*.json"):
        with file_path.open("r",encoding="utf-8") as f:
            pair = json.load(f)

        zh_path = Path(pair["zh_page_path"])

        es_path = Path(pair["es_page_path"])

        with zh_path.open("r",encoding="utf-8") as f:
            zh_page = json.load(f)

        with es_path.open("r",encoding="utf-8") as f:
            es_page = json.load(f)

        zh_texts = extract_top_texts(
            zh_page,
            top_n
        )

        es_texts = extract_top_texts(
            es_page,
            top_n
        )

        similarity = emb_similarity(
            zh_texts,
            es_texts
        )

        pair["emb_verif_similarity"] = similarity

        with file_path.open("w",encoding="utf-8") as f:
            json.dump(
                pair,
                f,
                ensure_ascii=False,
                indent=2
            )

        results.append(
            (
                file_path,
                similarity
            )
        )

    return results