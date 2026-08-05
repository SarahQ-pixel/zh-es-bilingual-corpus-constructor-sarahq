from pathlib import Path
import json
import random
import yaml


def load_config():
    with open("config/evaluator_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def reservoir_sample_idx(idx_input_path,sample_size,seed):
    random.seed(seed)
    reservoir = []

    with open(idx_input_path,"r",encoding="utf-8") as f:
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


def load_sentences_by_ids(input_path,required_ids):
    result = {}

    with open(input_path,"r",encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            sentence_id = record["sentence_id"]
            if sentence_id in required_ids:
                result[sentence_id] = record["text"]

    return result


def write_parallel_corpus(selected_alignments,src_sentences,tgt_sentences,output_src_path,output_tgt_path):
    output_src_path = Path(output_src_path)
    output_tgt_path = Path(output_tgt_path)

    output_src_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_tgt_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with(
        open(output_src_path,"w",encoding="utf-8",newline="") as src_file,
        open(output_tgt_path,"w",encoding="utf-8",newline="") as tgt_file
    ): 
        for alignment in selected_alignments:
            src_ids = alignment["src_sentence_ids"]
            tgt_ids = alignment["tgt_sentence_ids"]
            for src_id in src_ids:
                src_text = src_sentences.get(
                    src_id,
                    ""
                )
                for tgt_id in tgt_ids:
                    tgt_text = tgt_sentences.get(
                        tgt_id,
                        ""
                    )
                    src_file.write(
                        src_text.replace("\n"," ")
                        +
                        "\n"
                    )
                    tgt_file.write(
                        tgt_text.replace("\n"," ")
                        +
                        "\n"
                    )


def sample_corpus(src_input_path,tgt_input_path,idx_input_path,output_src_path,output_tgt_path,test_pairs):
    config = load_config()
    seed = config["sample_corpus_final"]["random_seed"]

    selected_alignments = reservoir_sample_idx(
        idx_input_path,
        test_pairs,
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

    write_parallel_corpus(
        selected_alignments,
        src_sentences,
        tgt_sentences,
        output_src_path,
        output_tgt_path
    )