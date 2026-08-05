from pathlib import Path
import hashlib
import json
import random
import yaml
from collections import deque


def load_config():
    with open("config/sentence_align_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def iter_xml_files(root_path, rng):
    root_path = Path(root_path)
    dir_queue = deque([root_path])
    file_iters = deque()

    while dir_queue or file_iters:
        while dir_queue:
            current_dir = dir_queue.popleft()
            try:
                entries = sorted(current_dir.iterdir(), key=lambda p: p.name)
            except Exception:
                continue

            rng.shuffle(entries)

            xml_files = []
            sub_dirs = []

            for e in entries:
                if e.is_dir():
                    sub_dirs.append(e)
                elif e.is_file() and e.suffix.lower() == ".xml":
                    xml_files.append(e)
            for d in sub_dirs:
                dir_queue.append(d)
            if xml_files:
                file_iters.append(iter(xml_files))
        if not file_iters:
            continue
        it = file_iters.popleft()
        try:
            f = next(it)
            yield f
            file_iters.append(it)
        except StopIteration:
            pass


def build_pair_id(a_path, b_path):
    raw_str = f"{a_path}||{b_path}"

    return hashlib.md5(raw_str.encode("utf-8")).hexdigest()


def page_selector(A_dir, B_dir, output_dir):
    config = load_config()

    prefix = config["page_selector_1t1"]["selected_pair_prefix"]
    max_pairs = config["page_selector_1t1"]["max_pairs"]
    seed = config["page_selector_1t1"]["random_seed"]
    rng = random.Random(seed)

    zh_lang = config["page_selector_1t1"]["zh_default_language"]
    es_lang = config["page_selector_1t1"]["es_default_language"]

    A_dir = Path(A_dir)
    B_dir = Path(B_dir)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0

    for a_file in iter_xml_files(A_dir, rng):
        if count >= max_pairs:
            break
        try:
            rel_path = a_file.relative_to(A_dir)
        except Exception:
            continue

        b_file = B_dir / rel_path

        if not b_file.exists():
            continue

        pair_id = build_pair_id(a_file, b_file)

        result = {
            "pair_id": pair_id,
            "zh_page_path": str(a_file),
            "zh_page_language": zh_lang,
            "es_page_path": str(b_file),
            "es_page_language": es_lang
        }

        file_name = f"{prefix}{pair_id}.json"
        out_path = output_dir / file_name

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        count += 1

    return count