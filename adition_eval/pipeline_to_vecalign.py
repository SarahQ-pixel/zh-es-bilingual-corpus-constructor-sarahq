
import json
from pathlib import Path

from .un_eval import postvecalign_to_vecalign, tei_to_text


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_project_path(file_path):
    """Resolve a file path relative to the project root."""

    normalized_path = str(file_path).replace("\\", "/")
    path = Path(normalized_path)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path


def inspect_document_pair(jsonl_path):
    """Read and validate the document pair in one pipeline JSONL file."""

    src_file = None
    tgt_file = None
    record_count = 0

    with Path(jsonl_path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}: {exc}"
                ) from exc

            record_count += 1

            current_src = record["src"]
            current_tgt = record["tgt"]

            if (
                current_src["language"] != "zh"
                or current_tgt["language"] != "es"
            ):
                raise ValueError(
                    "Expected pipeline alignment order zh->es, "
                    f"got {current_src['language']}->"
                    f"{current_tgt['language']}."
                )

            current_src_file = current_src["file_path"]
            current_tgt_file = current_tgt["file_path"]

            if src_file is None:
                src_file = current_src_file
                tgt_file = current_tgt_file

            elif (
                current_src_file != src_file
                or current_tgt_file != tgt_file
            ):
                raise ValueError(
                    "The input JSONL contains multiple document pairs. "
                    "Each input file must correspond to one document pair."
                )

    if record_count == 0:
        raise ValueError(
            f"No alignment records found in {jsonl_path}"
        )

    return {
        "src_file": src_file,
        "tgt_file": tgt_file,
        "record_count": record_count,
    }


def convert_pipeline_file(input_jsonl, output_align, src_file_filtro=None):
    """Convert one pipeline JSONL document pair to Vecalign format."""

    input_jsonl = Path(input_jsonl)
    output_align = Path(output_align)

    if not input_jsonl.is_file():
        raise FileNotFoundError(
            f"Pipeline JSONL file not found: {input_jsonl}"
        )

    # Identify the original TEI document paths from the JSONL records.
    pair_info = inspect_document_pair(input_jsonl)

    src_tei_path = resolve_project_path(
        pair_info["src_file"]
    )
    tgt_tei_path = resolve_project_path(
        pair_info["tgt_file"]
    )

    for tei_path in (src_tei_path, tgt_tei_path):
        if not tei_path.is_file():
            raise FileNotFoundError(
                f"TEI file not found: {tei_path}"
            )

    # Extract the sentences and build the sentence-ID mappings.
    zh_lines, zh_map = tei_to_text(src_tei_path)
    es_lines, es_map = tei_to_text(tgt_tei_path)

    print(f"Chinese: {len(zh_lines)} sentences")
    print(f"Spanish: {len(es_lines)} sentences")
    print()

    print("Chinese mapping (sentence_id -> line index):")
    print("  ", zh_map)
    print()

    # Convert the original pipeline JSONL directly.
    test, stats = postvecalign_to_vecalign(
        input_jsonl,
        zh_map,
        es_map,
        output_align,
        src_file_filtro=src_file_filtro,
    )

    print("Conversion statistics:")
    for key, value in stats.items():
        print(f"   {key:28} {value}")

    print()
    print("Hypothesis (zh->es):")
    for alignment in test:
        print("   ", alignment)

    return {
        "input": str(input_jsonl),
        "output": str(output_align),
        "src_file": pair_info["src_file"],
        "tgt_file": pair_info["tgt_file"],
        "record_count": pair_info["record_count"],
        "converted_alignment_count": len(test),
        "conversion_stats": stats,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Convert one pipeline JSONL document pair "
            "to Vecalign alignment format."
        )
    )

    parser.add_argument(
        "input_jsonl",
        help="Pipeline JSONL file for one document pair.",
    )

    parser.add_argument(
        "output_align",
        help="Output Vecalign alignment file.",
    )

    parser.add_argument(
        "--src-file-filtro",
        default="corr_1",
        help="Optional substring filter for the source file path.",
    )

    args = parser.parse_args()

    summary = convert_pipeline_file(
        input_jsonl=args.input_jsonl,
        output_align=args.output_align,
        src_file_filtro=args.src_file_filtro,
    )

    print()
    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )
