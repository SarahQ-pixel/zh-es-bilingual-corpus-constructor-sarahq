from pathlib import Path, PurePosixPath

from .un_eval import linkgrp_info, links_to_vecalign, tei_to_text, transpose, escribir_filas


def get_document_language(document_path):
    """Identify the language from an LNK document path."""

    normalized = str(document_path).replace("\\", "/")
    parts = PurePosixPath(normalized).parts

    if len(parts) < 2:
        raise ValueError(
            f"Unsupported document path in LNK: {document_path}"
        )

    if parts[0] == "Xml":
        language = parts[1]
    else:
        language = parts[0]

    if language not in ("es", "zh"):
        raise ValueError(
            f"Unsupported language in LNK path: {language}"
        )

    return language


def validate_lnk_documents(info, lnk_path):
    """Validate the language pair and document paths in an LNK file."""

    from_doc = info["fromDoc"]
    to_doc = info["toDoc"]

    from_language = get_document_language(from_doc)
    to_language = get_document_language(to_doc)

    if {from_language, to_language} != {"es", "zh"}:
        raise ValueError(
            f"The LNK does not contain a zh-es pair: {lnk_path}"
        )

    from_parts = PurePosixPath(
        str(from_doc).replace("\\", "/")
    ).parts

    to_parts = PurePosixPath(
        str(to_doc).replace("\\", "/")
    ).parts

    # Compare the relative document paths after the language directory.
    from_relative = (
        from_parts[2:] if from_parts[0] == "Xml"
        else from_parts[1:]
    )
    to_relative = (
        to_parts[2:] if to_parts[0] == "Xml"
        else to_parts[1:]
    )

    if from_relative != to_relative:
        raise ValueError(
            "The LNK source and target do not identify the same "
            f"relative document: {from_doc} / {to_doc}"
        )

    return from_language, to_language


def convert_lnk_file(
    es_tei_path,
    es_txt_path,
    zh_tei_path,
    zh_txt_path,
    input_lnk_path,
    gold_zh_es_path,
):
    """Convert one UN LNK file into a zh-es Vecalign alignment file."""

    es_tei_path = Path(es_tei_path)
    es_txt_path = Path(es_txt_path)
    zh_tei_path = Path(zh_tei_path)
    zh_txt_path = Path(zh_txt_path)
    input_lnk_path = Path(input_lnk_path)
    gold_zh_es_path = Path(gold_zh_es_path)

    # Check the input files.
    for input_path in (
        es_tei_path,
        zh_tei_path,
        input_lnk_path,
    ):
        if not input_path.is_file():
            raise FileNotFoundError(
                f"Input file not found: {input_path}"
            )

    # Extract the Spanish and Chinese sentences.
    es_lines, es_map = tei_to_text(
        es_tei_path,
        es_txt_path,
    )

    zh_lines, zh_map = tei_to_text(
        zh_tei_path,
        zh_txt_path,
    )

    print(f"Spanish: {len(es_lines)} sentences")
    print(f"Chinese: {len(zh_lines)} sentences")
    print()

    print("Spanish mapping (sentence_id -> line index):")
    print("  ", es_map)
    print()

    # Read the document-level information from the LNK file.
    groups = linkgrp_info(input_lnk_path)

    if not groups:
        raise ValueError(
            f"No linkGrp information found: {input_lnk_path}"
        )

    if len(groups) != 1:
        raise ValueError(
            f"Expected one linkGrp in {input_lnk_path}, "
            f"found {len(groups)}"
        )

    info = groups[0]

    print("Document-level score:")
    print("  ", info)
    print()

    # Identify the original alignment direction.
    from_language, to_language = validate_lnk_documents(
        info,
        input_lnk_path,
    )

    print(f"fromDoc = {info['fromDoc']}")
    print(f"toDoc   = {info['toDoc']}")
    print(f"Original order: {from_language}->{to_language}")
    print()

    # Select the sentence-ID mappings according to the LNK order.
    if from_language == "es":
        from_map = es_map
        to_map = zh_map
    else:
        from_map = zh_map
        to_map = es_map

    # Convert the LNK links into Vecalign format.
    # src_id2idx corresponds to fromDoc, while tgt_id2idx corresponds
    # to toDoc. Empty-side alignments are excluded for this experiment.
    gold_from_to, stats = links_to_vecalign(
        input_lnk_path,
        from_map,
        to_map,
        out_path=None,
        keep_empty_side=False,
    )

    print("Conversion statistics:")
    for key, value in stats.items():
        print(f"   {key:28} {value}")
    print()

    print(
        f"Gold alignments in original order "
        f"({from_language}->{to_language}):"
    )
    for alignment in gold_from_to:
        print("   ", alignment)

    # Normalize the alignment direction to zh -> es.
    if from_language == "es":
        gold_zh_es = transpose(gold_from_to)
        print("\n-> Transposing to zh->es")
    else:
        gold_zh_es = list(gold_from_to)
        print("\n-> Already in zh->es order; no transposition needed")

    # Write the final alignment file.
    escribir_filas(gold_zh_es, gold_zh_es_path)

    print()
    print("Final gold alignments (zh->es):")
    for alignment in gold_zh_es[:5]:
        print("   ", alignment)

    print()
    print(f"Chinese-to-Spanish gold: {gold_zh_es_path}")

    return {
        "input_lnk": str(input_lnk_path),
        "original_order": f"{from_language}->{to_language}",
        "final_order": "zh->es",
        "alignment_count": len(gold_zh_es),
        "gold_zh_es": str(gold_zh_es_path),
        "transposed": from_language == "es",
        "conversion_stats": stats,
        "es_lines": es_lines,
        "zh_lines": zh_lines,
    }