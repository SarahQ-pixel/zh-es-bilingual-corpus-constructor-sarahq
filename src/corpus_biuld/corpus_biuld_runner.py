import core.bootstrap

import json
import yaml
import importlib
from pathlib import Path
from collections import OrderedDict


def load_config():
    with open("config/corpus_biuld_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_extractor(document_format, document_lang_mod):
    module_name = (
        f"src.corpus_biuld."
        f"corpus_biuld_{document_format}_{document_lang_mod}"
    )

    try:
        module = importlib.import_module(module_name)

    except ModuleNotFoundError:
        raise Exception(
            f"Unsupported corpus builder: "
            f"{document_format}_{document_lang_mod}"
        )

    return module.load_document, module.get_sentence


def create_document_cache(max_size):
    return OrderedDict(), max_size


def get_cached_document(cache,max_size,file_path,load_document):
    file_path = str(Path(file_path))

    if file_path in cache:
        cache.move_to_end(file_path)
        return cache[file_path]

    document = load_document(file_path)

    cache[file_path] = document
    cache.move_to_end(file_path)

    if len(cache) > max_size:
        cache.popitem(last=False)

    return document


def iter_jsonl(jsonl_path):
    with open(jsonl_path,"r",encoding="utf-8") as f:

        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def append_jsonl(jsonl_path, record):
    with open(jsonl_path,"a",encoding="utf-8") as f:

        f.write(
            json.dumps(
                record,
                ensure_ascii=False
            )
        )

        f.write("\n")


def append_idx(idx_path, record):
    with open(idx_path,"a",encoding="utf-8") as f:

        f.write(
            json.dumps(
                record,
                ensure_ascii=False
            )
        )

        f.write("\n")


def restore_sentence(
        side_data,
        sentence_cache,
        next_sentence_id,
        document_cache,
        document_cache_size,
        load_document,
        get_sentence,
        output_jsonl):
    new_sentence_ids = []

    file_path = side_data["file_path"]
    language = side_data["language"]

    document = get_cached_document(
        document_cache,
        document_cache_size,
        file_path,
        load_document
    )

    for sentence in side_data["sentences"]:
        source_sentence_id = sentence["sentence_id"]
        cache_key = (
            str(file_path),
            str(source_sentence_id)
        )
        if cache_key in sentence_cache:
            new_sentence_ids.append(
                sentence_cache[cache_key]
            )
            continue

        text = get_sentence(
            document,
            source_sentence_id,
            language
        )

        record = {
            "sentence_id": next_sentence_id,
            "language": language,
            "text": text,
            "metadata": {
                "file_path": file_path,
                "source_sentence_id": source_sentence_id
            }
        }

        append_jsonl(
            output_jsonl,
            record
        )

        sentence_cache[cache_key] = next_sentence_id

        new_sentence_ids.append(
            next_sentence_id
        )

        next_sentence_id += 1

    return (
        new_sentence_ids,
        next_sentence_id
    )


def corpus_biuld_runner():
    config = load_config()

    document_format = config["corpus_biuld_runner"]["document_format"]
    document_lang_mod = config["corpus_biuld_runner"]["document_lang_mod"]

    load_document, get_sentence = load_extractor(
        document_format,
        document_lang_mod
    )

    input_jsonl = Path(
        config["corpus_biuld_runner"]["input"]["align_sentences_path"][document_lang_mod]
    )

    output_dir = Path(
        config["corpus_biuld_runner"]["output"]["aligned_sentences_dir"][document_lang_mod]
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    src_output = (output_dir / (config["corpus_biuld_runner"]["output"]["src_sentences_doc_name"] + ".jsonl"))

    tgt_output = (output_dir / (config["corpus_biuld_runner"]["output"]["tgt_sentences_doc_name"]+ ".jsonl"))

    idx_output = (output_dir / (config["corpus_biuld_runner"]["output"]["align_idx_doc_name"]+ ".idx"))

    for path in (src_output,tgt_output,idx_output):
        if path.exists():
            path.unlink()

    src_sentence_cache = {}

    tgt_sentence_cache = {}

    src_next_sentence_id = config["corpus_biuld_runner"]["src_sentence_start_id"]

    tgt_next_sentence_id = config["corpus_biuld_runner"]["tgt_sentence_start_id"]

    (document_cache,document_cache_size) = create_document_cache(
        config["corpus_biuld_runner"]["document_cache_size"]
    )

    for record in iter_jsonl(input_jsonl):
        (src_sentence_ids,src_next_sentence_id) = restore_sentence(
            record["src"],
            src_sentence_cache,
            src_next_sentence_id,
            document_cache,
            document_cache_size,
            load_document,
            get_sentence,
            src_output
        )

        (tgt_sentence_ids,tgt_next_sentence_id) = restore_sentence(
            record["tgt"],
            tgt_sentence_cache,
            tgt_next_sentence_id,
            document_cache,
            document_cache_size,
            load_document,
            get_sentence,
            tgt_output
        )
        idx_record = {
            "alignment_id": record["alignment_id"],
            "src_sentence_ids": src_sentence_ids,
            "tgt_sentence_ids": tgt_sentence_ids,
            "alignment_score": record["alignment_score"]
        }

        append_idx(
            idx_output,
            idx_record
        )


if __name__ == "__main__":
    corpus_biuld_runner()