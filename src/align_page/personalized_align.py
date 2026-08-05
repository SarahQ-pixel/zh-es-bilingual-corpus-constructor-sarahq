import json
import yaml
from pathlib import Path


def load_config():
    with open("config/align_page_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()


def extract_chunks(page: dict):
    return page.get("chunks", [])


def chunk_match_score(c1: dict, c2: dict):
    tag_weight = config["personalized_align"]["tag_weight"]
    depth_weight = config["personalized_align"]["depth_weight"]
    content_weight = config["personalized_align"]["is_content_weight"]

    score = 0.0

    if c1.get("tag") == c2.get("tag"):
        score += tag_weight

    if c1.get("depth") == c2.get("depth"):
        score += depth_weight

    if c1.get("is_content") == c2.get("is_content"):
        score += content_weight

    return score


def dp_align(zh_chunks, es_chunks):
    n, m = len(zh_chunks), len(es_chunks)
    dp = []
    for i in range(n + 1):
        row = []
        for j in range(m + 1):
            row.append(0.0)
        dp.append(row)

    for i in range(1, n + 1): 
        for j in range(1, m + 1): 
            match_score = chunk_match_score(
                zh_chunks[i - 1], 
                es_chunks[j - 1]
            )
            dp[i][j] = max(
                dp[i - 1][j], 
                dp[i][j - 1], 
                dp[i - 1][j - 1] + match_score 
            )
    return dp[n][m]


def normalizator(score, zh_chunks, es_chunks):
    max_possible = max(len(zh_chunks), len(es_chunks))
    if max_possible == 0:
        return 0.0
    return score / max_possible


def personalized_align_sim_cal(candidates_dir: Path):
    results = []

    for file_path in candidates_dir.glob("*.json"):
        with file_path.open("r", encoding="utf-8") as f:
            pair = json.load(f)

        zh_path = Path(pair["zh_page_path"])
        es_path = Path(pair["es_page_path"])

        with zh_path.open("r", encoding="utf-8") as f:
            zh_page = json.load(f)

        with es_path.open("r", encoding="utf-8") as f:
            es_page = json.load(f)

        zh_chunks = extract_chunks(zh_page)
        es_chunks = extract_chunks(es_page)

        raw_score = dp_align(zh_chunks, es_chunks)

        print("Nomalizatior start") #TEST

        similarity = normalizator(raw_score, zh_chunks, es_chunks)

        pair["personalized_align_similarity"] = similarity

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(pair, f, ensure_ascii=False, indent=2)

        results.append((file_path, similarity))

    return results