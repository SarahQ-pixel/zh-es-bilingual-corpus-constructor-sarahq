from pathlib import Path
import json
import csv
import random
import yaml


def load_config():
    with open("config/evaluator_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def reservoir_sample_idx(idx_input_path, sample_size, seed):
    random.seed(seed)
    reservoir = []

    with open(idx_input_path, "r", encoding="utf-8") as f:
        for index, line in enumerate(f):
            record = json.loads(line)
            if index < sample_size:
                reservoir.append(record)
            else:
                random_index = random.randint(0,index)
                if random_index < sample_size:
                    reservoir[random_index] = record

    return reservoir


def collect_required_sentence_ids(selected_alignments):
    src_ids = set()
    tgt_ids = set()

    for record in selected_alignments:
        src_ids.update(
            record["src_sentence_ids"]
        )
        tgt_ids.update(
            record["tgt_sentence_ids"]
        )

    return src_ids, tgt_ids


def load_sentences_by_ids(input_path, required_ids):
    result = {}

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            sentence_id = record["sentence_id"]
            if sentence_id in required_ids:
                result[sentence_id] = record["text"]

    return result


def expand_alignment_records(selected_alignments,src_sentences,tgt_sentences):
    expanded = []
    for alignment in selected_alignments:
        alignment_id = alignment["alignment_id"]
        src_ids = alignment["src_sentence_ids"]
        tgt_ids = alignment["tgt_sentence_ids"]
        for src_id in src_ids:
            for tgt_id in tgt_ids:
                expanded.append(
                    {
                        "alignment_id": alignment_id,
                        "src_sentence_id": src_id,
                        "tgt_sentence_id": tgt_id,
                        "src_text": src_sentences.get(
                            src_id,
                            ""
                        ),
                        "tgt_text": tgt_sentences.get(
                            tgt_id,
                            ""
                        ),
                    }
                )

    return expanded


def write_csv(output_path, records):
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = [
        "alignment_id",
        "src_sentence_id",
        "tgt_sentence_id",
        "src_text",
        "tgt_text",
        "human_check",
        "comment",
    ]

    with open(output_path,"w",encoding="utf-8-sig",newline="") as f:
        writer = csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "alignment_id": record["alignment_id"],
                    "src_sentence_id": record["src_sentence_id"],
                    "tgt_sentence_id": record["tgt_sentence_id"],
                    "src_text": record["src_text"],
                    "tgt_text": record["tgt_text"],
                    "human_check": "",
                    "comment": "",
                }
            )


def sample_corpus(src_input_path,tgt_input_path,idx_input_path,output_path,manual_pairs):
    config = load_config()
    seed = config["sample_manual_check"]["random_seed"]

    selected_alignments = reservoir_sample_idx(
        idx_input_path,
        manual_pairs,
        seed
    )

    src_ids, tgt_ids = (
        collect_required_sentence_ids(
            selected_alignments
        )
    )

    src_sentences = load_sentences_by_ids(
        src_input_path,
        src_ids
    )

    tgt_sentences = load_sentences_by_ids(
        tgt_input_path,
        tgt_ids
    )

    expanded_records = expand_alignment_records(
        selected_alignments,
        src_sentences,
        tgt_sentences
    )

    write_csv(
        output_path,
        expanded_records
    )