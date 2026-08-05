from pathlib import Path
import yaml
import sacrebleu


def load_config():
    with open("config/evaluator_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_sentences(file_path):
    sentences = []

    with open(file_path,"r",encoding="utf-8") as f:
        for line in f:
            sentences.append(
                line.rstrip("\n")
            )

    return sentences


def get_bleu_tokenizer(lang):
    lang = lang.lower()

    tokenizer_map = {
        "zh": "zh",
        "en": "13a",
        "fr": "13a",
        "es": "13a",
        "ru": "13a",
        "ar": "13a",
        "de": "13a",
        "pt": "13a",
        "it": "13a"
    }

    if lang not in tokenizer_map:
        raise ValueError(
            f"Unsupported BLEU language: {lang}. "
            "Supported languages are: "
            "zh, en, fr, es, ru, ar, de, pt, it."
        )

    return tokenizer_map[lang]


def calculate_bleu(prediction_path,reference_path):
    config = load_config()

    lang = config["bleu_score"]["lang"]

    tokenize = get_bleu_tokenizer(lang)

    predictions = load_sentences(
        Path(prediction_path)
    )

    references = load_sentences(
        Path(reference_path)
    )

    if len(predictions) != len(references):
        raise ValueError(
            "Prediction and reference "
            "sentence numbers are different."
        )

    bleu = sacrebleu.corpus_bleu(
        predictions,
        [
            references
        ],
        tokenize=tokenize
    )

    result = {
        "score":bleu.score,
        "counts":bleu.counts,
        "totals":bleu.totals,
        "precisions":bleu.precisions,
        "bp":bleu.bp,
        "sys_len":bleu.sys_len,
        "ref_len":bleu.ref_len,
        "tokenize":tokenize,
        "sacrebleu_version":sacrebleu.__version__
    }

    return result