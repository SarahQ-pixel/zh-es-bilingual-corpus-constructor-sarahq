import json
import yaml

from pathlib import Path
from datasketch import MinHash, MinHashLSH


def load_config():
    with open("config/deduplicator_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()


def init_union_find():
    return {}


def find_root(parent, item):
    if parent[item] != item:
        parent[item] = find_root(
            parent,
            parent[item],
        )

    return parent[item]


def union(parent, item_a, item_b):
    if item_a not in parent:
        parent[item_a] = item_a

    if item_b not in parent:
        parent[item_b] = item_b

    root_a = find_root(
        parent,
        item_a,
    )

    root_b = find_root(
        parent,
        item_b,
    )

    if root_a != root_b:
        parent[root_b] = root_a


def build_groups(parent):
    groups = {}

    for item in parent:
        root = find_root(
            parent,
            item,
        )
        if root not in groups:
            groups[root] = []
        groups[root].append(item)

    return [
        group
        for group in groups.values()
        if len(group) > 1
    ]


def build_minhash(shingles):
    minhash = MinHash(num_perm=config["minhash_dedup"]["num_perm"])

    for shingle in shingles:
        minhash.update(
            shingle.encode("utf-8")
        )

    return minhash


def read_jsonl_record(input_path):
    input_path = Path(input_path)

    with input_path.open("r",encoding="utf-8",) as f:
        for line in f:
            yield json.loads(line)


def deduplicator(input_path):
    lsh = MinHashLSH(
        threshold=config["minhash_dedup"]["threshold"],
        num_perm=config["minhash_dedup"]["num_perm"],
    )

    parent = init_union_find()

    for record in read_jsonl_record(input_path):
        sentence_id = record["sentence_id"]
        shingles = record["shingles"]
        current_minhash = build_minhash(
            shingles
        )
        if sentence_id not in parent:
            parent[sentence_id] = sentence_id
        similar_items = lsh.query(
            current_minhash
        )
        for item in similar_items:
            union(
                parent,
                sentence_id,
                item,
            )
        lsh.insert(
            sentence_id,
            current_minhash,
        )

    return build_groups(parent)