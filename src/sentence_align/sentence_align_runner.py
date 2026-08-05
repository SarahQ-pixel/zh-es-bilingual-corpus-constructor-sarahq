import core.bootstrap

import json
import yaml
import importlib
from pathlib import Path

from src.sentence_align.page_selector_1t1 import page_selector
from src.sentence_align.vecalign_runner import run_vecalign


def load_config():
    with open("config/sentence_align_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_extractor(document_format, document_lang_mod):
    module_name = (
        f"src.sentence_align."
        f"extract_{document_format}_{document_lang_mod}"
    )

    try:
        module = importlib.import_module(module_name)

    except ModuleNotFoundError:
        raise Exception(
            f"Extractor not found: {module_name}.py"
        )

    func_name = f"extract_{document_format}"

    if not hasattr(module, func_name):
        raise Exception(
            f"Function {func_name} not found in {module_name}.py"
        )

    return getattr(module, func_name)


def restore_sentence_ids(indices, corresp):
    result = []

    for idx in indices:
        if idx in corresp:
            result.append(
                {
                    "sentence_id": corresp[idx]
                }
            )

    return result


def get_last_alignment_id(jsonl_path):
    if not jsonl_path.exists():
        return 0

    if jsonl_path.stat().st_size == 0:
        return 0

    with open(jsonl_path,"rb") as f:
        f.seek(0, 2)
        position = f.tell()
        buffer = b""
        while position > 0:
            position -= 1
            f.seek(position)
            char = f.read(1)
            if char == b"\n":
                if buffer:
                    break
            else:
                buffer = char + buffer

    if not buffer:
        return 0

    last_line = buffer.decode(
        "utf-8"
    )

    data = json.loads(last_line)

    return int(
        data["alignment_id"]
    )


def append_jsonl(jsonl_path, records):
    jsonl_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(jsonl_path,"a",encoding="utf-8") as f:
        for record in records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
            )

            f.write("\n")


def sentence_align_runner():
    config = load_config()

    document_format = config["sentence_align_runner"]["document_format"]
    document_lang_mod = config["sentence_align_runner"]["document_lang_mod"]

    extract_func = load_extractor(
        document_format,
        document_lang_mod
    )

    tasks = []

    if document_lang_mod == "1t2":
        segmented_pages_dir = Path(
            config["sentence_align_runner"]["input"]["1t2"]["segmented_pages_dir"]
        )
        for json_file in sorted(segmented_pages_dir.glob("*")):
            tasks.append(
                {
                    "mode": "1t2",
                    "json_path": json_file
                }
            )

    elif document_lang_mod == "1t1":
        zh_dir = Path(config["sentence_align_runner"]["input"]["1t1"]["zh_segmentated_pages_dir"])
        es_dir = Path(config["sentence_align_runner"]["input"]["1t1"]["es_segmentated_pages_dir"])
        selected_pair_dir = Path(
            config["sentence_align_runner"]["input"]["1t1"]["selected_pair_dir"]
        )
        page_selector(
            zh_dir,
            es_dir,
            selected_pair_dir
        )
        for pair_json in sorted(selected_pair_dir.glob("*.json")):
            with open(pair_json,"r",encoding="utf-8") as f:
                pair_info = json.load(f)
            tasks.append(
                {
                    "mode": "1t1",
                    "pair_info": pair_info
                }
            )

    else:
        raise Exception(
            f"Unsupported document_lang_mod: {document_lang_mod}"
        )

    output_dir = Path(
        config["sentence_align_runner"]["output"]["aligned_sentences_dir"][document_lang_mod]
    )

    output_name = (
        config["sentence_align_runner"]["output"]["aligned_doc_name"] + ".jsonl"
    )

    output_path = output_dir / output_name

    max_pairs = config["sentence_align_runner"]["max_pairs"]

    next_alignment_id = (
        get_last_alignment_id(output_path) + 1
    )

    current_pairs = next_alignment_id - 1

    for task in tasks:
        if current_pairs >= max_pairs:
            break
        if task["mode"] == "1t2":
            json_path = task["json_path"]
            (
                zh_sentences_li,
                zh_corresp,
                es_sentences_li,
                es_corresp
            ) = extract_func(json_path)

            with open(json_path,"r",encoding="utf-8") as f:
                page_info = json.load(f)

            metadata = {
                "src_file": str(json_path),
                "tgt_file": str(json_path),
                "src_language": page_info["zh_page_language"],
                "tgt_language": page_info["es_page_language"],
                "page_path": str(json_path)
            }

        else:
            pair_info = task["pair_info"]
            (
                zh_sentences_li,
                zh_corresp,
                es_sentences_li,
                es_corresp
            ) = extract_func(
                pair_info["zh_page_path"],
                pair_info["es_page_path"]
            )

            metadata = {
                "src_file": pair_info["zh_page_path"],
                "tgt_file": pair_info["es_page_path"],
                "src_language": pair_info["zh_page_language"],
                "tgt_language": pair_info["es_page_language"],
                "page_path": str(pair_info["zh_page_path"])
            }

        zh_corresp = dict(zh_corresp)
        es_corresp = dict(es_corresp)

        vecalign_result = run_vecalign(
            zh_sentences_li,
            es_sentences_li
        )

        records = []

        alignments = vecalign_result["alignments"]
        scores = vecalign_result["scores"]

        for alignment, score in zip(alignments, scores):
            src_indices = alignment[0]
            tgt_indices = alignment[1]
            if not src_indices or not tgt_indices:
                continue
            record = {
                "alignment_id": str(next_alignment_id),

                "vecalign_alignment": {
                    "src_indices": src_indices,
                    "tgt_indices": tgt_indices,
                    "raw_tuple":
                        json.dumps(
                            {
                                "src": src_indices,
                                "tgt": tgt_indices
                            },
                            ensure_ascii=False
                        )
                },

                "src": {
                    "file_path": metadata["src_file"],
                    "language": metadata["src_language"],
                    "sentences":
                        restore_sentence_ids(
                            src_indices,
                            zh_corresp
                        )
                },

                "tgt": {
                    "file_path": metadata["tgt_file"],
                    "language": metadata["tgt_language"],
                    "sentences":
                        restore_sentence_ids(
                            tgt_indices,
                            es_corresp
                        )

                },

                "alignment_score": score
            }

            records.append(record)

            next_alignment_id += 1
            current_pairs += 1

            if current_pairs >= max_pairs:
                break

        append_jsonl(
            output_path,
            records
        )
        if current_pairs >= max_pairs:
            break


if __name__ == "__main__":
    sentence_align_runner()