import core.bootstrap

from pathlib import Path
import yaml

from src.evaluator.sample_manual_check import sample_corpus as sample_manual
from src.evaluator.sample_corpus_final import sample_corpus as sample_final
from src.evaluator.sample_corpus_refer import sample_corpus as sample_refer
from src.evaluator.sample_corpus_test import sample_corpus as sample_test
from src.evaluator.train_lm import train_model
from src.evaluator.bleu_score import calculate_bleu


def load_config():
    with open("config/evaluator_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_file_path(directory,filename,suffix):
    return (Path(directory) / f"{filename}{suffix}")


def save_bleu_result(output_path,title,result,mode="w"):
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path,mode,encoding="utf-8") as f:
        if mode == "a":
            f.write("\n\n")
        f.write(f"{title}\n")
        f.write(
            "=" * len(title)
            +
            "\n"
        )
        for key, value in result.items():
            f.write(
                f"{key}: {value}\n"
            )


def evaluator_runner():
    config = load_config()

    corpus_final_src = build_file_path(
        config["input"]["corpus_final"]["input_dir"],
        config["input"]["corpus_final"]["src_doc_name"],
        ".jsonl"
    )

    corpus_final_tgt = build_file_path(
        config["input"]["corpus_final"]["input_dir"],
        config["input"]["corpus_final"]["tgt_doc_name"],
        ".jsonl"
    )

    corpus_final_idx = build_file_path(
        config["input"]["corpus_final"]["input_dir"],
        config["input"]["corpus_final"]["idx_doc_name"],
        ".idx"
    )

    corpus_test_src = build_file_path(
        config["input"]["corpus_test"]["input_dir"],
        config["input"]["corpus_test"]["src_doc_name"],
        ".jsonl"
    )

    corpus_test_tgt = build_file_path(
        config["input"]["corpus_test"]["input_dir"],
        config["input"]["corpus_test"]["tgt_doc_name"],
        ".jsonl"
    )

    corpus_test_idx = build_file_path(
        config["input"]["corpus_test"]["input_dir"],
        config["input"]["corpus_test"]["idx_doc_name"],
        ".idx"
    )

    corpus_refer_input = config["input"]["corpus_refer"]["input_path"]

    manual_output = build_file_path(
        config["output"]["manual"]["dir"],
        config["output"]["manual"]["doc_name"],
        ".csv"
    )

    corpus_final_sampled_src = build_file_path(
        config["evaluator_runner"]["corpus_final_sampled"]["dir"],
        config["evaluator_runner"]["corpus_final_sampled"]["src_doc_name"],
        ".txt"
    )

    corpus_final_sampled_tgt = build_file_path(
        config["evaluator_runner"]["corpus_final_sampled"]["dir"],
        config["evaluator_runner"]["corpus_final_sampled"]["tgt_doc_name"],
        ".txt"
    )

    corpus_refer_sampled_src = build_file_path(
        config["evaluator_runner"]["corpus_refer_sampled"]["dir"],
        config["evaluator_runner"]["corpus_refer_sampled"]["src_doc_name"],
        ".txt"
    )

    corpus_refer_sampled_tgt = build_file_path(
        config["evaluator_runner"]["corpus_refer_sampled"]["dir"],
        config["evaluator_runner"]["corpus_refer_sampled"]["tgt_doc_name"],
        ".txt"
    )

    corpus_test_sampled_src = build_file_path(
        config["evaluator_runner"]["corpus_test_sampled"]["dir"],
        config["evaluator_runner"]["corpus_test_sampled"]["src_doc_name"],
        ".txt"
    )

    corpus_test_sampled_tgt = build_file_path(
        config["evaluator_runner"]["corpus_test_sampled"]["dir"],
        config["evaluator_runner"]["corpus_test_sampled"]["tgt_doc_name"],
        ".txt"
    )

    corpus_final_prediction = build_file_path(
        config["output"]["tgt_prediction"]["dir"],
        config["output"]["tgt_prediction"]["corpus_final_doc_name"],
        ".txt"
    )

    corpus_refer_prediction = build_file_path(
        config["output"]["tgt_prediction"]["dir"],
        config["output"]["tgt_prediction"]["corpus_refer_doc_name"],
        ".txt"
    )

    bleu_output = build_file_path(
        config["output"]["bleu"]["dir"],
        config["output"]["bleu"]["doc_name"],
        ".txt"
    )

    sample_manual(
        corpus_final_src,
        corpus_final_tgt,
        corpus_final_idx,
        manual_output,
        config["evaluator_runner"]["manual_pairs"]
    )

    sample_final(
        corpus_final_src,
        corpus_final_tgt,
        corpus_final_idx,
        corpus_final_sampled_src,
        corpus_final_sampled_tgt,
        config["evaluator_runner"]["train_pairs"]
    )

    sample_refer(
        corpus_refer_input,
        corpus_refer_sampled_src,
        corpus_refer_sampled_tgt,
        config["evaluator_runner"]["train_pairs"]
    )

    sample_test(
        corpus_test_src,
        corpus_test_tgt,
        corpus_test_idx,
        corpus_test_sampled_src,
        corpus_test_sampled_tgt,
        config["evaluator_runner"]["test_pairs"]
    )

    train_model(
        corpus_final_sampled_src,
        corpus_final_sampled_tgt,
        corpus_test_sampled_src,
        corpus_final_prediction
    )

    train_model(
        corpus_refer_sampled_src,
        corpus_refer_sampled_tgt,
        corpus_test_sampled_src,
        corpus_refer_prediction
    )

    bleu_final = calculate_bleu(
        corpus_final_prediction,
        corpus_test_sampled_tgt
    )

    save_bleu_result(
        bleu_output,
        "Bleu information of corpus_final",
        bleu_final,
        mode="w"
    )

    bleu_refer = calculate_bleu(
        corpus_refer_prediction,
        corpus_test_sampled_tgt
    )

    save_bleu_result(
        bleu_output,
        "Bleu information of corpus_refer",
        bleu_refer,
        mode="a"
    )


if __name__ == "__main__":
    evaluator_runner()