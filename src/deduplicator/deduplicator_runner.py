import core.bootstrap

from pathlib import Path
import json
import yaml
import importlib

from src.deduplicator.shingle_generator import shingle_generator_runner


def load_config():
    with open("config/deduplicator_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_deduplicator(name):
    module_name = (f"src.deduplicator.{name}_dedup")

    module = importlib.import_module(
        module_name
    )

    return module.deduplicator


def build_file_path(directory,filename,suffix):
    return (Path(directory) / f"{filename}{suffix}")


def build_statistics():
    return {
        "original_count": 0,
        "removed_count": 0,
        "remaining_count": 0,
    }


def stream_generate_shingles(input_path,output_path):
    input_path = Path(input_path)

    with input_path.open("r",encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            shingle_generator_runner(
                record["sentence_id"],
                record["text"],
                output_path,
            )


def collect_discard_sentence_ids(shingle_path,deduplicator_name):
    deduplicator = load_deduplicator(deduplicator_name)
    similar_groups = deduplicator(shingle_path)

    discard_sentence_ids = []

    for group in similar_groups:
        for sentence_id in group[1:]:
            discard_sentence_ids.append(
                sentence_id
            )

    return discard_sentence_ids


def filter_parallel_corpus(
    src_input_path,
    tgt_input_path,
    idx_input_path,
    src_output_path,
    tgt_output_path,
    idx_output_path,
    lang_side,
    discard_sentence_ids,
):
    discard_sentence_ids = set(discard_sentence_ids)

    statistics = build_statistics()

    src_input_path = Path(src_input_path)
    tgt_input_path = Path(tgt_input_path)
    idx_input_path = Path(idx_input_path)

    src_output_path = Path(src_output_path)
    tgt_output_path = Path(tgt_output_path)
    idx_output_path = Path(idx_output_path)

    with(
        open(src_input_path, "r", encoding="utf-8") as src_in,
        open(tgt_input_path, "r", encoding="utf-8") as tgt_in,
        open(idx_input_path, "r", encoding="utf-8") as idx_in,
        open(src_output_path, "a", encoding="utf-8") as src_out,
        open(tgt_output_path, "a", encoding="utf-8") as tgt_out,
        open(idx_output_path, "a", encoding="utf-8") as idx_out,
    ):
        for src_line, tgt_line, idx_line in zip(
            src_in,
            tgt_in,
            idx_in,
        ):
            statistics["original_count"] += 1
            idx_record = json.loads(
                idx_line
            )
            if lang_side == "src":
                sentence_ids = (idx_record["src_sentence_ids"])
            else:
                sentence_ids = (idx_record["tgt_sentence_ids"])
            should_remove = any(
                sentence_id
                in discard_sentence_ids
                for sentence_id in sentence_ids
            )
            if should_remove:
                statistics["removed_count"] += 1
                continue
            src_out.write(src_line)
            tgt_out.write(tgt_line)
            idx_out.write(idx_line)
            statistics["remaining_count"] += 1

    return statistics

def print_statistics(statistics):
    print("===== DEDUPLICATOR RESULT =====")

    for key, value in statistics.items():
        print(
            f"{key}: {value}"
        )

def deduplicator_runner():
    config = load_config()

    lang_side = config["deduplicator_runner"]["lang_side"]
    input_dir = config["input"]["input_dir"]
    output_dir = config["output"]["output_dir"]

    if lang_side == "src":
        dedup_input_path = build_file_path(
            input_dir,
            config["input"]["src_doc_name"],
            ".jsonl"
        )

    else:
        dedup_input_path = build_file_path(
            input_dir,
            config["input"]["tgt_doc_name"],
            ".jsonl"
        )

    shingle_output_path = build_file_path(
        config["deduplicator_runner"]["sentence_shingles_doc_dir"],
        config["deduplicator_runner"]["sentence_shingles_doc_name"],
        ".jsonl"
    )

    stream_generate_shingles(
        dedup_input_path,
        shingle_output_path,
    )

    discard_sentence_ids = (
        collect_discard_sentence_ids(
            shingle_output_path,
            config["deduplicator_runner"]["deduplicator"]
        )
    )

    src_input_path = build_file_path(
        input_dir,
        config["input"]["src_doc_name"],
        ".jsonl"
    )

    tgt_input_path = build_file_path(
        input_dir,
        config["input"]["tgt_doc_name"],
        ".jsonl"
    )

    idx_input_path = build_file_path(
        input_dir,
        config["input"]["idx_doc_name"],
        ".idx"
    )

    src_output_path = build_file_path(
        output_dir,
        config["output"]["src_doc_name"],
        ".jsonl"
    )

    tgt_output_path = build_file_path(
        output_dir,
        config["output"]["tgt_doc_name"],
        ".jsonl"
    )

    idx_output_path = build_file_path(
        output_dir,
        config["output"]["idx_doc_name"],
        ".idx"
    )

    statistics = filter_parallel_corpus(
        src_input_path,
        tgt_input_path,
        idx_input_path,
        src_output_path,
        tgt_output_path,
        idx_output_path,
        lang_side,
        discard_sentence_ids,
    )

    print_statistics(
    statistics
    )


if __name__ == "__main__":
    deduplicator_runner()