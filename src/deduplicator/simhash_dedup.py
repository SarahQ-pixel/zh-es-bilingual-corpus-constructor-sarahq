from pathlib import Path
import json
import yaml

from simhash import Simhash
from simhash import SimhashIndex


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

    item_a = int(item_a)
    item_b = int(item_b)

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


def build_simhash(shingles):
    return Simhash(shingles)


def read_jsonl_record(input_path):
    input_path = Path(input_path)

    with input_path.open("r",encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def deduplicator(input_path):
    parent = init_union_find()

    simhash_items = []

    for record in read_jsonl_record(input_path):
        sentence_id = record["sentence_id"]
        shingles = record["shingles"]
        fingerprint = build_simhash(
            shingles
        )
        if sentence_id not in parent:
            parent[sentence_id] = sentence_id
        simhash_items.append(
            (
                str(sentence_id),
                fingerprint,
            )
        )

    index = SimhashIndex(
        simhash_items,
        k=config["simhash_dedup"]["distance"],
    )

    for sentence_id, fingerprint in simhash_items:
        current_sentence_id = int(sentence_id)
        similar_items = index.get_near_dups(
            fingerprint
        )
        for item in similar_items:
            similar_sentence_id = int(item)
            if similar_sentence_id == current_sentence_id:
                continue
            union(
                parent,
                sentence_id,
                item,
            )

    return build_groups(parent)