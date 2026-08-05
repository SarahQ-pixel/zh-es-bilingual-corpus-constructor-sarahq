import json
import math
import yaml
from pathlib import Path


def load_config():
    with open("config/align_page_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()


def extract_chunks(page: dict):
    return page.get("chunks", [])


def compute_length_threshold(chunks):
    raw_lengths = []

    config = load_config()
    percentile = config["length_align"]["min_length_percentile"]

    for c in chunks:
        length = c.get("text_length")
        if length is None:
            continue
        raw_lengths.append(length)

    if not raw_lengths:
        return None

    sorted_lengths = sorted(raw_lengths)

    index = int(len(sorted_lengths) * percentile)
    index = min(index, len(sorted_lengths) - 1)

    return sorted_lengths[index]


def extract_valid_lengths(chunks, threshold):
    lengths = []

    for c in chunks:
        length = c.get("text_length")
        if length is None:
            continue
        if length < threshold:
            continue
        lengths.append(math.log(length + 1))

    return lengths


def dp_length_align(zh_lengths, es_lengths):

    n, m = len(zh_lengths), len(es_lengths)

    dp = []
    for i in range(n + 1):
        row = []
        for j in range(m + 1):
            row.append(0.0)
        dp.append(row)

    def match_score(a, b):
        diff = abs(a - b)
        return 1.0 / (1.0 + diff)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            score = match_score(
                zh_lengths[i - 1],
                es_lengths[j - 1]
            )
            dp[i][j] = max(
                dp[i - 1][j],
                dp[i][j - 1],
                dp[i - 1][j - 1] + score
            )

    return dp[n][m]


def normalize(score, zh_lengths, es_lengths):
    max_possible = max(len(zh_lengths), len(es_lengths))

    if max_possible == 0:
        return 0.0

    return score / max_possible


def length_align_sim_cal(candidates_dir: Path):
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

        zh_threshold = compute_length_threshold(zh_chunks)
        es_threshold = compute_length_threshold(es_chunks)

        zh_lengths = extract_valid_lengths(zh_chunks, zh_threshold)
        es_lengths = extract_valid_lengths(es_chunks, es_threshold)

        if len(zh_lengths) == 0 or len(es_lengths) == 0:
            similarity = 0.0
        else:
            raw_score = dp_length_align(zh_lengths, es_lengths)
            similarity = normalize(raw_score, zh_lengths, es_lengths)

        pair["length_align_similarity"] = similarity

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(pair, f, ensure_ascii=False, indent=2)

        results.append((file_path, similarity))

    return results