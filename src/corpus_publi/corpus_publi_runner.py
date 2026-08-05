import core.bootstrap

from pathlib import Path
import json
import yaml


def load_config():
    with open("config/corpus_publi_config.yaml","r",encoding="utf-8",) as f:
        return yaml.safe_load(f)


def build_path(directory, name, suffix):
    return Path(directory) / f"{name}.{suffix}"


def clean_sentence_jsonl(input_path, output_path):
    with (
        open(input_path, "r", encoding="utf-8") as infile,
        open(output_path, "w", encoding="utf-8") as outfile
    ):
        for line in infile:
            record = json.loads(line)
            record.pop("metadata", None)
            outfile.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )


def clean_alignment_idx(input_path, output_path):
    with (
        open(input_path, "r", encoding="utf-8") as infile,
        open(output_path, "w", encoding="utf-8") as outfile
    ):
        for line in infile:
            record = json.loads(line)
            record.pop("alignment_score", None)
            outfile.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )


def corpus_publi_runner():
    config = load_config()

    input_dir = Path(config["input"]["input_dir"])
    output_dir = Path(config["output"]["output_dir"])

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    input_src_path = build_path(
        input_dir,
        config["input"]["src_doc_name"],
        "jsonl"
    )

    input_tgt_path = build_path(
        input_dir,
        config["input"]["tgt_doc_name"],
        "jsonl"
    )

    input_idx_path = build_path(
        input_dir,
        config["input"]["idx_doc_name"],
        "idx"
    )

    output_src_path = build_path(
        output_dir,
        config["output"]["src_doc_name"],
        "jsonl"
    )

    output_tgt_path = build_path(
        output_dir,
        config["output"]["tgt_doc_name"],
        "jsonl"
    )

    output_idx_path = build_path(
        output_dir,
        config["output"]["idx_doc_name"],
        "idx"
    )

    for path in [
        output_src_path,
        output_tgt_path,
        output_idx_path,
    ]:
        path.touch(exist_ok=True)

    clean_sentence_jsonl(
        input_src_path,
        output_src_path,
    )

    clean_sentence_jsonl(
        input_tgt_path,
        output_tgt_path,
    )

    clean_alignment_idx(
        input_idx_path,
        output_idx_path,
    )


if __name__ == "__main__":
    corpus_publi_runner()
