# Combination of the processing logic from external/vecalign/vecalign.py and processing in src/sentence_align/overlap_perso.py, because this part avoids an I/O-based pipeline design.
import yaml
import numpy as np

from src.sentence_align.vecalign_perso import vecalign
from src.sentence_align.dp_utils_perso import (make_alignment_types,make_one_to_many_alignment_types)
from src.sentence_align.overlap_perso import compute_overlap_embeddings


def load_config():
    with open("config/sentence_align_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_vecs(overlaps, embeddings, num_overlaps, num_sentences, dim):
    vecs = np.zeros((num_overlaps, num_sentences, dim), dtype=np.float32)
    idx = 0

    for depth in range(num_overlaps):
        layer_len = num_sentences - depth
        if layer_len < 1:
            layer_len = 1
        for j in range(layer_len):
            if idx >= len(embeddings):
                raise ValueError("Embedding index overflow in build_vecs")
            vecs[depth, j, :] = embeddings[idx]
            idx += 1

    return vecs


def run_vecalign(src_sentences, tgt_sentences):
    config = load_config()

    src_overlaps, src_emb, num_overlaps = compute_overlap_embeddings(src_sentences)
    tgt_overlaps, tgt_emb, _ = compute_overlap_embeddings(tgt_sentences)

    dim = src_emb.shape[1]
    n_src = len(src_sentences)
    n_tgt = len(tgt_sentences)

    vecs0 = build_vecs(
        src_overlaps,
        src_emb,
        num_overlaps,
        n_src,
        dim
    )
    vecs1 = build_vecs(
        tgt_overlaps,
        tgt_emb,
        num_overlaps,
        n_tgt,
        dim
    )

    if config.get("one_to_many") is not None:
        alignment_types = make_one_to_many_alignment_types(
            config["vecalign_runner"]["one_to_many"]
        )
    else:
        alignment_types = make_alignment_types(
            config["vecalign_runner"]["alignment_max_size"]
        )

    del_percentile_frac = config["vecalign_runner"]["del_percentile_frac"]
    width_over2 = config["vecalign_runner"]["search_buffer_size"]
    max_size_full_dp = config["vecalign_runner"]["max_size_full_dp"]
    costs_sample_size = config["vecalign_runner"]["costs_sample_size"]
    num_samps_for_norm = config["vecalign_runner"]["num_samps_for_norm"]

    stack = vecalign(
        vecs0=vecs0,
        vecs1=vecs1,
        final_alignment_types=alignment_types,
        del_percentile_frac=del_percentile_frac,
        width_over2=width_over2,
        max_size_full_dp=max_size_full_dp,
        costs_sample_size=costs_sample_size,
        num_samps_for_norm=num_samps_for_norm
    )

    result = {
        "alignments": stack[0]["final_alignments"],
        "scores": stack[0]["alignment_scores"]
    }

    return result