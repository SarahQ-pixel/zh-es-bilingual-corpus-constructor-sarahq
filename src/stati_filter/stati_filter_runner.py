import core.bootstrap

import json
from pathlib import Path
import yaml

from src.stati_filter.text_cleaner import clean_text
from src.stati_filter.pair_eliminator import should_keep_pair


def load_config():
    with open("config/stati_filter_config.yaml","r",encoding="utf-8",) as f:
        return yaml.safe_load(f)


def build_file_path(directory, file_name, suffix):
    directory = Path(directory)

    return directory / f"{file_name}{suffix}"


def ensure_output_directory(output_dir):
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_json_line(line):
    return json.loads(line)


def write_json_line(file, data):
    json.dump(
        data,
        file,
        ensure_ascii=False,
    )

    file.write("\n")


def build_statistics():
    return {
        "total_pairs": 0,
        "kept_pairs": 0,
        "removed_pairs": 0,
        "removed_by_url": 0,
        "removed_by_email": 0,
        "removed_by_src_length": 0,
        "removed_by_tgt_length": 0,
        "html_cleaned": 0,
        "css_cleaned": 0,
        "javascript_cleaned": 0,
        "whitespace_normalized": 0,
    }


def update_clean_statistics(statistics,clean_stats):
    if clean_stats["html_removed"]:
        statistics["html_cleaned"] += 1

    if clean_stats["css_removed"]:
        statistics["css_cleaned"] += 1

    if clean_stats["javascript_removed"]:
        statistics["javascript_cleaned"] += 1

    if clean_stats["whitespace_normalized"]:
        statistics["whitespace_normalized"] += 1



def update_remove_statistics(statistics,reason):
    statistics["removed_pairs"] += 1

    if reason == "url":
        statistics["removed_by_url"] += 1

    elif reason == "email":
        statistics["removed_by_email"] += 1

    elif reason == "src_length":
        statistics["removed_by_src_length"] += 1

    elif reason == "tgt_length":
        statistics["removed_by_tgt_length"] += 1


def check_remaining_lines(src_file,tgt_file,idx_file,):
    src_extra = next(src_file,None)

    tgt_extra = next(tgt_file,None)

    idx_extra = next(idx_file,None,)

    if (src_extra is not None or tgt_extra is not None or idx_extra is not None):
        raise ValueError(
            "Input files do not have the same number of records."
        )


def process_documents(config):
    input_dir = Path(config["input"]["input_dir"])
    output_dir = Path(config["output"]["output_dir"])

    ensure_output_directory(output_dir)

    input_src_path = build_file_path(
        input_dir,
        config["input"]["src_doc_name"],
        ".jsonl"
    )

    input_tgt_path = build_file_path(
        input_dir,
        config["input"]["tgt_doc_name"],
        ".jsonl"
    )

    input_idx_path = build_file_path(
        input_dir,
        config["input"]["idx_doc_name"],
        ".idx"
    )

    output_src_path = build_file_path(
        output_dir,
        config["output"]["src_doc_name"],
        ".jsonl"
    )

    output_tgt_path = build_file_path(
        output_dir,
        config["output"]["tgt_doc_name"],
        ".jsonl"
    )

    output_idx_path = build_file_path(
        output_dir,
        config["output"]["idx_doc_name"],
        ".idx"
    )

    statistics = build_statistics()

    with(
        open(input_src_path,"r",encoding="utf-8") as src_file,
        open(input_tgt_path,"r",encoding="utf-8",) as tgt_file,
        open(input_idx_path,"r",encoding="utf-8",) as idx_file,
        open(output_src_path,"w",encoding="utf-8",) as src_output,
        open(output_tgt_path,"w",encoding="utf-8",) as tgt_output,
        open(output_idx_path,"w",encoding="utf-8",) as idx_output
    ): 
        for src_line, tgt_line, idx_line in zip(
            src_file,
            tgt_file,
            idx_file,
        ):
            statistics["total_pairs"] += 1
            src_item = load_json_line(
                src_line
            )
            tgt_item = load_json_line(
                tgt_line
            )
            idx_item = load_json_line(
                idx_line
            )
            src_text, src_clean_stats = clean_text(
                src_item["text"],
                config,
            )
            tgt_text, tgt_clean_stats = clean_text(
                tgt_item["text"],
                config,
            )
            update_clean_statistics(
                statistics,
                src_clean_stats,
            )
            update_clean_statistics(
                statistics,
                tgt_clean_stats,
            )
            keep, reason = should_keep_pair(
                src_text,
                tgt_text,
                config,
            )
            if not keep:
                update_remove_statistics(
                    statistics,
                    reason,
                )
                continue
            src_item["text"] = src_text
            tgt_item["text"] = tgt_text
            write_json_line(
                src_output,
                src_item,
            )
            write_json_line(
                tgt_output,
                tgt_item,
            )
            write_json_line(
                idx_output,
                idx_item,
            )
            statistics["kept_pairs"] += 1
        check_remaining_lines(
            src_file,
            tgt_file,
            idx_file,
        )

    return statistics


def print_statistics(statistics):
    print(
        "===== STATI FILTER RESULT ====="
    )
    for key, value in statistics.items():
        print(
            f"{key}: {value}"
        )


def stati_filter_runner():
    config = load_config()

    statistics = process_documents(
        config
    )

    print_statistics(
        statistics
    )


if __name__ == "__main__":
    stati_filter_runner()