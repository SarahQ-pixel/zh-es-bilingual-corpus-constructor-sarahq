#Combination of the processing logic from external/vecalign/overlap.py and processing in src/sentence_align/sentence_emb.py, because this part avoids an I/O-based pipeline design.
from src.sentence_align.sentence_emb import encode
import yaml


def load_config():
    with open("config/sentence_align_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def preprocess_sentences(sentences, enable_cleaning=True, blank_token="BLANK_LINE"):
    if not enable_cleaning:
        return sentences
    cleaned = []

    for s in sentences:
        if s is None:
            cleaned.append(blank_token)
            continue
        s = str(s).strip()
        if len(s) == 0:
            cleaned.append(blank_token)
        else:
            cleaned.append(s)

    return cleaned


def build_overlaps(sentences, num_overlaps=4):
    overlaps = []
    n = len(sentences)

    for k in range(1, num_overlaps + 1):

        layer_out = ['PAD'] * min(k - 1, n)

        for i in range(n - k + 1):
            chunk = " ".join(sentences[i:i + k])
            layer_out.append(chunk)

        overlaps.extend(layer_out)

    return overlaps


def truncate_overlaps(overlaps, max_char_length=10000):
    if max_char_length is None:
        return overlaps

    return [o[:max_char_length] for o in overlaps]


def compute_overlap_embeddings(sentences):
    config = load_config()

    sentences = preprocess_sentences(
        sentences,
        enable_cleaning=config["overlap_perso"]["enable_cleaning"],
        blank_token=config["overlap_perso"]["blank_token"]
    )

    num_overlaps = config["overlap_perso"]["num_overlaps"]

    overlaps = build_overlaps(
        sentences,
        num_overlaps=num_overlaps
    )

    embeddings = encode(
        overlaps,
        show_progress_bar=False
    )

    return overlaps, embeddings, num_overlaps


def merge_overlap_results(overlaps_a, overlaps_b):
    return {
        "source_overlaps": overlaps_a,
        "target_overlaps": overlaps_b
    }