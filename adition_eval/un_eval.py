
"""
Utilities for evaluating the pipeline's sentence-alignment stage
against the link files of the UN Parallel Corpus v1.0.

This module is intended to live in adition_eval/, outside src/,
as a supplementary evaluation toolkit.

It does not modify Vecalign's implementation. It imports the
original score_multiple and read_alignments functions.
"""

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from vecalign.score import score_multiple
from vecalign.dp_utils import read_alignments


# ---------------------------------------------------------------
# General utilities


def _localname(tag):
    """Return an XML tag's local name, without its namespace."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _fmt(s, t, cost=0):
    """Format one alignment in Vecalign's alignment-file format."""
    return f"{sorted(s)}:{sorted(t)}:{cost}"


# ---------------------------------------------------------------
# 1. TEI -> text and sentence-ID mapping


def tei_to_text(tei_path, out_txt=None):
    """
    Extract sentences from a UN Corpus TEI document in document order.

    Returns:
        lines: Sentence texts in document order.
        id2idx: Mapping from each sentence's XML ID ("paragraph:sentence")
                to its zero-based line index.

    If out_txt is provided, write one sentence per line. The resulting
    file can be supplied to Vecalign as --src or --tgt, ensuring that
    gold links and predicted links use the same index space.

    Supports TEI and TEI.2 documents, with or without XML namespaces.
    """
    tei_path = Path(tei_path)

    tree = ET.parse(tei_path)
    lines = []
    id2idx = {}

    xml_id_attribute = "{http://www.w3.org/XML/1998/namespace}id"

    for element in tree.iter():
        if _localname(element.tag) != "s":
            continue

        sentence_id = (
            element.get("id")
            or element.get(xml_id_attribute)
        )

        if sentence_id is None:
            continue

        if sentence_id in id2idx:
            raise ValueError(
                f"Duplicate sentence ID in {tei_path}: {sentence_id}"
            )

        id2idx[sentence_id] = len(lines)
        lines.append(
            " ".join("".join(element.itertext()).split())
        )

    if out_txt is not None:
        out_txt = Path(out_txt)
        out_txt.parent.mkdir(parents=True, exist_ok=True)

        with out_txt.open("w", encoding="utf-8", newline="\n") as file:
            file.write("\n".join(lines) + "\n")

    return lines, id2idx


def linkgrp_info(links_path):
    """
    Return the fromDoc, toDoc, and document-level score of each linkGrp.

    The document-level score is the main indicator to consider when
    selecting reference files. An individual link score does not
    necessarily guarantee that the corresponding alignment is correct.
    """
    links_path = Path(links_path)

    tree = ET.parse(links_path)
    results = []

    groups = [
        element
        for element in tree.iter()
        if _localname(element.tag) == "linkGrp"
    ]

    for element in groups:
        score = element.get("score")

        results.append({
            "fromDoc": element.get("fromDoc"),
            "toDoc": element.get("toDoc"),
            "score": float(score) if score is not None else None,
        })

    return results


# ---------------------------------------------------------------
# 2. UN links -> Vecalign format


def links_to_vecalign(
    links_path,
    src_id2idx,
    tgt_id2idx,
    out_path=None,
    min_link_score=None,
    keep_empty_side=True,
):
    """
    Convert a UN Corpus .lnk file to Vecalign's alignment format.

    src_id2idx and tgt_id2idx must correspond to the fromDoc and toDoc
    sides of the .lnk file, respectively.

    IMPORTANT:
    In UN Corpus .lnk files, the left side of xtargets corresponds to
    toDoc, while the right side corresponds to fromDoc.
    Therefore, the output is generated in the fromDoc -> toDoc order.

    min_link_score:
        Optional threshold for individual link scores. Links without
        a score are counted in the statistics. Insertion and deletion
        links may have a score of zero, so a positive threshold can
        remove them.

    keep_empty_side:
        If True, retain links with an empty source or target side
        (1-0 or 0-1). If False, discard them.

    Returns:
        rows: Alignment lines in Vecalign format.
        stats: Counts of processed, skipped, and written links.

    Unknown sentence IDs are counted in stats["id_desconocido"].
    If this value is greater than zero, the links and TEI documents
    must be checked rather than silently ignoring the discrepancy.
    """
    links_path = Path(links_path)

    tree = ET.parse(links_path)
    rows = []
    stats = Counter()

    for element in tree.iter():
        if _localname(element.tag) != "link":
            continue

        xtargets = element.get("xtargets")

        if xtargets is None:
            continue

        stats["total"] += 1

        if min_link_score is not None:
            score = element.get("score")

            if score is None:
                stats["sin_score"] += 1
            elif float(score) < min_link_score:
                stats["bajo_umbral"] += 1
                continue

        left_ids, _, right_ids = xtargets.partition(";")
        left_sentence_ids = left_ids.split()
        right_sentence_ids = right_ids.split()

        # The left side corresponds to toDoc and the right side to fromDoc.
        # Check sentence IDs against their corresponding mappings.
        unknown_ids = []

        for sentence_id in left_sentence_ids:
            if sentence_id not in tgt_id2idx:
                unknown_ids.append(("toDoc", sentence_id))

        for sentence_id in right_sentence_ids:
            if sentence_id not in src_id2idx:
                unknown_ids.append(("fromDoc", sentence_id))

        if unknown_ids:
            stats["id_desconocido"] += 1

            print("\n[WARNING] Unknown sentence ID detected.")
            print(f"  LNK file: {links_path}")
            print(f"  xtargets: {xtargets}")
            print("  Unknown sentence IDs:")

            for side, sentence_id in unknown_ids:
                print(f"    - {side}: {sentence_id}")

            print(f"  Link attributes: {element.attrib}")

            continue

        # Generate the output in the fromDoc -> toDoc order.
        s = [
            src_id2idx[sentence_id]
            for sentence_id in right_sentence_ids
        ]
        t = [
            tgt_id2idx[sentence_id]
            for sentence_id in left_sentence_ids
        ]

        if not s and not t:
            stats["vacios"] += 1
            continue

        if not keep_empty_side and (not s or not t):
            stats["lado_vacio_descartado"] += 1
            continue

        cost = float(element.get("score", 0))
        rows.append(_fmt(s, t, cost))
        stats["escritos"] += 1
        stats[f"tipo_{len(s)}-{len(t)}"] += 1

    if out_path is not None:
        escribir_filas(rows, out_path)

    return rows, dict(stats)


# ---------------------------------------------------------------
# 3. Transpose alignment sides


def transpose(filas):
    """
    Reverse the source and target sides of Vecalign alignment lines.

    This is necessary when the reference links run from Spanish to
    Chinese while the pipeline uses Chinese-to-Spanish alignments.
    Without transposition, precision and recall can be interchanged
    without producing an explicit error.
    """
    salida = []

    for linea in filas:
        s, t, *resto = linea.strip().split(":")
        cost = resto[0] if resto else "0"
        salida.append(f"{t.strip()}:{s.strip()}:{cost}")

    return salida


def leer_filas(path):
    """Read a file of alignment lines into a list of strings."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        return [
            line.strip()
            for line in file
            if line.strip()
        ]


def escribir_filas(filas, path):
    """Write alignment lines to a UTF-8 text file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(filas) + "\n")


# ---------------------------------------------------------------
# 4. Pipeline post-Vecalign output -> Vecalign format


def postvecalign_to_vecalign(
    jsonl_path,
    src_id2idx,
    tgt_id2idx,
    out_path=None,
    src_file_filtro=None,
):
    """
    Convert the pipeline's intermediate output after Vecalign to
    Vecalign's alignment-file format.

    Uses the sentence_id values preserved in each record (e.g. "2:1"),
    NOT the pipeline's internal src_indices/tgt_indices. Sentence IDs
    allow the reference and prediction to share the same index space.

    Expected JSONL record structure:
        {
            "alignment_id": "1",
            "src": {
                "file_path": "...zh...xml",
                "sentences": [{"sentence_id": "2:1"}]
            },
            "tgt": {
                "file_path": "...es...xml",
                "sentences": [{"sentence_id": "3:1"}]
            },
            "alignment_score": 0.118
        }

    src_file_filtro:
        Optional substring used to select records belonging to a
        particular source document (e.g. "pv_759"). This is necessary
        when the JSONL file contains records from multiple document pairs.

    Returns:
        filas: Converted alignment lines.
        stats: Counts of processed, skipped, and written records.
    """
    jsonl_path = Path(jsonl_path)

    filas = []
    stats = Counter()

    with jsonl_path.open("r", encoding="utf-8") as file:
        for linea in file:
            linea = linea.strip()

            if not linea:
                continue

            reg = json.loads(linea)
            stats["total"] += 1

            ruta_src = (reg.get("src") or {}).get("file_path", "")

            if (
                src_file_filtro
                and src_file_filtro not in ruta_src
            ):
                stats["fuera_del_filtro"] += 1
                continue

            ids_s = [
                sentence["sentence_id"]
                for sentence in (reg.get("src") or {}).get("sentences", [])
            ]

            ids_t = [
                sentence["sentence_id"]
                for sentence in (reg.get("tgt") or {}).get("sentences", [])
            ]

            try:
                s = [
                    src_id2idx[sentence_id]
                    for sentence_id in ids_s
                ]
                t = [
                    tgt_id2idx[sentence_id]
                    for sentence_id in ids_t
                ]
            except KeyError:
                stats["id_desconocido"] += 1
                continue

            if not s and not t:
                stats["vacios"] += 1
                continue

            filas.append(
                _fmt(s, t, reg.get("alignment_score", 0) or 0)
            )
            stats["escritos"] += 1

    if out_path is not None:
        escribir_filas(filas, out_path)

    return filas, dict(stats)


# ---------------------------------------------------------------
# 5. Scoring


def puntuar(test_path, gold_path):
    """
    Calculate strict and lax precision, recall, and F1 using
    Vecalign's original scoring implementation.

    Returns the dictionary produced by score_multiple:
        precision_strict, recall_strict, f1_strict,
        precision_lax, recall_lax, f1_lax.
    """
    test_path = Path(test_path)
    gold_path = Path(gold_path)

    return score_multiple(
        gold_list=[read_alignments(str(gold_path))],
        test_list=[read_alignments(str(test_path))],
    )


def tabla_metricas(res):
    """Format the metrics dictionary as a fixed-width text table."""
    out = [
        f"{'':10}{'Precision':>11}{'Recall':>10}{'F1':>10}"
    ]

    for m in ("strict", "lax"):
        out.append(
            f"{m:10}{res[f'precision_{m}']:>11.3f}"
            f"{res[f'recall_{m}']:>10.3f}"
            f"{res[f'f1_{m}']:>10.3f}"
        )

    return "\n".join(out)


# ---------------------------------------------------------------
# 6. Export alignment discrepancies for manual review


def _parse(linea):
    """Parse a Vecalign alignment line into source and target tuples."""
    s, t, *_ = linea.strip().split(":")
    return tuple(json.loads(s)), tuple(json.loads(t))


def volcar_discrepancias(
    test_path,
    gold_path,
    src_lines,
    tgt_lines,
    out_txt,
    etiqueta="",
):
    """
    Write alignments present in only one of the two files to a text
    report, including the sentence text on both sides.

    The report is intended for manual review. Since UN Corpus reference
    links may contain errors, a raw F1 score alone cannot distinguish
    pipeline errors from reference errors.

    Returns the discrepancy records as dictionaries.
    """
    test_path = Path(test_path)
    gold_path = Path(gold_path)
    out_txt = Path(out_txt)

    test = [
        _parse(line)
        for line in leer_filas(test_path)
    ]

    gold = [
        _parse(line)
        for line in leer_filas(gold_path)
    ]

    set_test = set(test)
    set_gold = set(gold)

    def texto(idxs, lineas):
        if not idxs:
            return "(no counterpart)"

        return " ⏎ ".join(
            lineas[i]
            if i < len(lineas)
            else f"<out-of-range index {i}>"
            for i in idxs
        )

    discrepancias = []

    for origen, propios, ajenos in (
        ("solo_en_pipeline", test, set_gold),
        ("solo_en_referencia", gold, set_test),
    ):
        for s, t in propios:
            if (s, t) not in ajenos:
                discrepancias.append({
                    "origen": origen,
                    "src_idx": list(s),
                    "tgt_idx": list(t),
                    "src_txt": texto(s, src_lines),
                    "tgt_txt": texto(t, tgt_lines),
                    "causa": "",
                    "nota": "",
                })

    out_txt.parent.mkdir(parents=True, exist_ok=True)

    with out_txt.open("w", encoding="utf-8", newline="\n") as file:
        file.write("=" * 78 + "\n")
        file.write(
            f"DISCREPANCIES FOR MANUAL REVIEW  {etiqueta}\n"
        )
        file.write(
            f"hypothesis: {test_path} ({len(test)} alignments)\n"
        )
        file.write(
            f"reference: {gold_path} ({len(gold)} alignments)\n"
        )
        file.write(
            f"discrepancies: {len(discrepancias)}\n"
        )
        file.write("=" * 78 + "\n\n")

        file.write(
            "For each case, record the CAUSE using one of these labels:\n"
        )

        for cod, desc in CAUSAS.items():
            file.write(f"  {cod:12} {desc}\n")

        file.write("\n" + "=" * 78 + "\n\n")

        for n, d in enumerate(discrepancias, 1):
            file.write(
                f"--- case {n:04d} [{d['origen']}] ---\n"
            )
            file.write(
                f"  src {d['src_idx']}: {d['src_txt']}\n"
            )
            file.write(
                f"  tgt {d['tgt_idx']}: {d['tgt_txt']}\n"
            )
            file.write(
                "  CAUSE: ____________    NOTE: \n\n"
            )

    return discrepancias


CAUSAS = {
    "PIPE-SEG": "Pipeline error: sentence segmentation",
    "PIPE-ALIGN": "Pipeline error: alignment (embeddings/DP)",
    "PIPE-GRAN": "Pipeline error: bead granularity (correct region)",
    "REF-SEG": "UN reference error: segmentation (line breaks, headings)",
    "REF-ALIGN": "UN reference error: offset or incorrect link",
    "REF-CONT": "Content difference between UN Parallel Corpus v1.0 language versions",
    "GRAN-COMP": "Granularity incompatibility between reference and pipeline",
    "TIPO-LONG": "Typological difference: Chinese/Spanish length ratio",
    "TIPO-PUNT": "Typological difference: punctuation",
    "TIPO-DISC": "Typological difference: discourse structure",
    "AMBIGUO": "Both interpretations are defensible",
}


# ---------------------------------------------------------------
# 7. Descriptive metrics without gold alignments


def descriptivas(align_path, n_src=None, n_tgt=None):
    """
    Calculate descriptive statistics from the alignment output alone.

    These are descriptive indicators, not accuracy metrics. The
    proportion of 1-1 beads is a direct measure of alignment granularity.
    It can be used to describe the Chinese-Spanish pair, but should not
    by itself be treated as proof of a typological explanation.
    """
    filas = leer_filas(align_path)
    al = []

    for linea in filas:
        partes = linea.split(":")
        s = json.loads(partes[0])
        t = json.loads(partes[1])
        c = float(partes[2]) if len(partes) > 2 else None

        al.append((s, t, c))

    beads = Counter(
        f"{len(s)}-{len(t)}"
        for s, t, _ in al
    )

    costos = [
        c
        for s, t, c in al
        if c is not None and s and t
    ]

    borrados = sum(
        1
        for s, t, _ in al
        if s and not t
    )

    inserciones = sum(
        1
        for s, t, _ in al
        if t and not s
    )

    cub_s = sum(
        len(s)
        for s, t, _ in al
        if t
    )

    cub_t = sum(
        len(t)
        for s, t, _ in al
        if s
    )

    total = len(al) or 1

    res = {
        "alineamientos": len(al),
        "beads": dict(beads.most_common()),
        "prop_1_1": round(beads.get("1-1", 0) / total, 4),
        "prop_fusiones_divisiones": round(
            sum(
                n
                for b, n in beads.items()
                if (
                    "-" in b
                    and b.split("-")[0] != b.split("-")[1]
                    and all(x != "0" for x in b.split("-"))
                )
            ) / total,
            4,
        ),
        "borrados": borrados,
        "inserciones": inserciones,
        "oraciones_src_cubiertas": cub_s,
        "oraciones_tgt_cubiertas": cub_t,
    }

    if n_src:
        res["cobertura_src"] = round(cub_s / n_src, 4)

    if n_tgt:
        res["cobertura_tgt"] = round(cub_t / n_tgt, 4)

    if costos:
        costos_ord = sorted(costos)
        k = len(costos_ord)

        res["costo_mediana"] = round(
            costos_ord[k // 2], 4
        )

        res["costo_p90"] = round(
            costos_ord[min(k - 1, int(0.9 * k))], 4
        )

        res["costo_max"] = round(costos_ord[-1], 4)

    return res


# ---------------------------------------------------------------
# 8. Length-based baseline for typological comparison


def baseline_longitud(
    src_lines,
    tgt_lines,
    out_path=None,
    max_bead=2,
):
    """
    Build a length-only alignment baseline using dynamic programming.

    This baseline is not intended to compete with Vecalign. It provides
    an empirical control for evaluating alignment behavior using
    sentence lengths alone.

    Allowed bead types include 1-1, 1-2, 2-1, 1-0, and 0-1, with
    multi-sentence beads limited by max_bead.

    Length is measured in characters. The average target/source length
    ratio is estimated from the document pair itself.
    """
    ls = [len(text) for text in src_lines]
    lt = [len(text) for text in tgt_lines]

    n = len(ls)
    m = len(lt)

    razon = (
        sum(lt) / sum(ls)
        if sum(ls)
        else 1.0
    )

    INF = float("inf")

    D = [
        [INF] * (m + 1)
        for _ in range(n + 1)
    ]

    back = [
        [None] * (m + 1)
        for _ in range(n + 1)
    ]

    D[0][0] = 0.0
    PEN_VACIO = 6.0

    def coste(i0, i1, j0, j1):
        a = sum(ls[i0:i1]) * razon
        b = sum(lt[j0:j1])

        if i1 == i0 or j1 == j0:
            return PEN_VACIO

        d = abs(a - b) / max(
            (a + b) / 2.0,
            1.0,
        )

        pen = 0.6 * (
            (i1 - i0) + (j1 - j0) - 2
        )

        return d + pen

    pasos = [(1, 1), (1, 0), (0, 1)]

    for di in range(1, max_bead + 1):
        for dj in range(1, max_bead + 1):
            if (di, dj) != (1, 1):
                pasos.append((di, dj))

    for i in range(n + 1):
        for j in range(m + 1):
            if D[i][j] == INF:
                continue

            for di, dj in pasos:
                ii = i + di
                jj = j + dj

                if ii > n or jj > m:
                    continue

                c = D[i][j] + coste(i, ii, j, jj)

                if c < D[ii][jj]:
                    D[ii][jj] = c
                    back[ii][jj] = (i, j, di, dj)

    filas = []
    i, j = n, m

    while (i, j) != (0, 0):
        paso = back[i][j]

        if paso is None:
            break

        pi, pj, di, dj = paso

        filas.append(
            _fmt(
                list(range(pi, pi + di)),
                list(range(pj, pj + dj)),
            )
        )

        i, j = pi, pj

    filas.reverse()

    if out_path is not None:
        escribir_filas(filas, out_path)

    return filas
    


if __name__ == "__main__":
    print("UN evaluation utilities loaded successfully.")
    print("Import this module and call the required evaluation functions.")
