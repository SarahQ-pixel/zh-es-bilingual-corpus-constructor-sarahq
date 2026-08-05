import core.bootstrap

import importlib
import json
from pathlib import Path
import yaml


def load_config():
    with open("config/lid_filter_config.yaml","r",encoding="utf-8",) as f:
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


def import_eliminator(lang):
    module_name = (
        f"src.lid_filter.{lang}_eliminator"
    )

    try:
        module = importlib.import_module(
            module_name
        )

    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            f"Cannot find eliminator module: {module_name}"
        )

    if not hasattr(module, "eliminate"):
        raise AttributeError(
            f"{module_name} does not provide eliminate() interface."
        )

    return module.eliminate


def build_statistics():
    return {
        "total_pairs": 0,
        "kept_pairs": 0,
        "removed_pairs": 0,
        "removed_by_src_side_eliminator": 0,
        "removed_by_tgt_side_eliminator": 0,
        "removed_by_both_side_eliminator": 0,
        "keep_rate": 0.0,
    }


def update_remove_statistics(statistics,src_removed,tgt_removed):
    statistics["removed_pairs"] += 1

    if src_removed and tgt_removed:
        statistics["removed_by_both_side_eliminator"] += 1

    elif src_removed:
        statistics["removed_by_src_side_eliminator"] += 1

    elif tgt_removed:
        statistics["removed_by_tgt_side_eliminator"] += 1


def check_remaining_lines(src_file,tgt_file,idx_file):
    src_extra = next(src_file, None)
    tgt_extra = next(tgt_file, None)
    idx_extra = next(idx_file, None)

    if ((src_extra is not None) or (tgt_extra is not None) or (idx_extra is not None)):
        raise ValueError(
            "Input files do not have the same number of records."
        )


def print_removed_pair(idx_item,src_debug,tgt_debug):
    print("Removed Pair:\n")

    print("Alignment:")
    print(
        json.dumps(
            idx_item,
            ensure_ascii=False,
            indent=4,
        )
    )

    print("\nSource Debug:")
    print(
        json.dumps(
            src_debug,
            ensure_ascii=False,
            indent=4,
        )
    )

    print("\nTarget Debug:")
    print(
        json.dumps(
            tgt_debug,
            ensure_ascii=False,
            indent=4,
        )
    )

    print(
        "================================================\n"
    )


def process_documents(config):
    input_dir = Path(
        config["input"]["input_dir"]
    )

    output_dir = Path(
        config["output"]["output_dir"]
    )

    ensure_output_directory(
        output_dir
    )

    src_lang = (
        config["lid_filter_runner"]["src_lang"]
    )

    tgt_lang = (
        config["lid_filter_runner"]["tgt_lang"]
    )

    src_eliminate = import_eliminator(
        src_lang
    )

    tgt_eliminate = import_eliminator(
        tgt_lang
    )

    input_src_path = build_file_path(
        input_dir,
        config["input"]["src_doc_name"],
        ".jsonl",
    )

    input_tgt_path = build_file_path(
        input_dir,
        config["input"]["tgt_doc_name"],
        ".jsonl",
    )

    input_idx_path = build_file_path(
        input_dir,
        config["input"]["idx_doc_name"],
        ".idx",
    )

    output_src_path = build_file_path(
        output_dir,
        config["output"]["src_doc_name"],
        ".jsonl",
    )

    output_tgt_path = build_file_path(
        output_dir,
        config["output"]["tgt_doc_name"],
        ".jsonl",
    )

    output_idx_path = build_file_path(
        output_dir,
        config["output"]["idx_doc_name"],
        ".idx",
    )

    statistics = build_statistics()

    with(
        open(input_src_path,"r",encoding="utf-8") as src_file,
        open(input_tgt_path,"r",encoding="utf-8") as tgt_file,
        open(input_idx_path,"r",encoding="utf-8") as idx_file,

        open(output_src_path,"w",encoding="utf-8") as src_output,
        open(output_tgt_path,"w",encoding="utf-8") as tgt_output,
        open(output_idx_path,"w",encoding="utf-8") as idx_output,
    ):
        for (src_line,tgt_line,idx_line) in zip(src_file,tgt_file,idx_file):
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
            src_removed, src_debug = src_eliminate(
                src_item["text"]
            )
            tgt_removed, tgt_debug = tgt_eliminate(
                tgt_item["text"]
            )
            if src_removed or tgt_removed:
                update_remove_statistics(
                    statistics,
                    src_removed,
                    tgt_removed,
                )
                print_removed_pair(
                    idx_item,
                    src_debug,
                    tgt_debug,
                )
                continue
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

    if statistics["total_pairs"] > 0:
        statistics["keep_rate"] = (
            statistics["kept_pairs"]
            /
            statistics["total_pairs"]
        )

    return statistics



def print_statistics(statistics):
    print(
        "===== LID FILTER RESULT ====="
    )

    for key,value in statistics.items():
        print(
            f"{key}: {value}"
        )


def lid_filter_runner():
    config = load_config()
    
    statistics = process_documents(
        config
    )

    print_statistics(
        statistics
    )


if __name__ == "__main__":

    lid_filter_runner()