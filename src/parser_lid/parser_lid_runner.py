#lxml parser and language identification runner
import core.bootstrap

import json
from pathlib import Path
import yaml

from src.parser_lid.lxml_parser import extract_info
from src.parser_lid.lid_url import iden_url
from src.parser_lid.lid_lm import iden_lm


def load_config():
    config_path = Path("config/parser_lid_config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def initialize_chunked_json(extracted_json_path: Path,output_dir: Path):
    print(f"INITIALIZING CHUNKED JSON for {extracted_json_path}") #TEST
    with open(extracted_json_path, "r", encoding="utf-8") as f:
        crawler_data = json.load(f)

    rendered_html_path = crawler_data["rendered_html_path"]

    doc_id = Path(rendered_html_path).stem

    parser_data = {
        "doc_id": doc_id,
        "extracted_pages_path": str(extracted_json_path),
        "url": crawler_data["url"],
        "url_segments": crawler_data.get(
            "url_segments",
            []
        ),
        "rendered_html_path": rendered_html_path,
        "stage_origin": "nnnn",
        "language": crawler_data.get(
            "language",
            "nnnn"
        ),
        "language_source": "nnnn",
        "chunks": [],
        "text": []
    }

    output_path = output_dir / extracted_json_path.name

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            parser_data,
            f,
            ensure_ascii=False,
            indent=2
        )

    return output_path


def process_chunked_json(chunked_json_path: Path):
    
    extract_info(
        str(chunked_json_path)
    )

    print(f"IDENTIFYING LANGUAGE for {chunked_json_path}") #TEST
    iden_url(
        str(chunked_json_path)
    )

    with open(
        chunked_json_path,
        "r",
        encoding="utf-8"
    ) as f:
        page_data = json.load(f)

    language_source = page_data.get(
        "language_source",
        "nnnn"
    )

    if language_source == "nnnn":
        print(f"LANGUAGE MODEL USED FOR THIS PAGE: {chunked_json_path}") #TEST
        iden_lm(
            str(chunked_json_path)
        )


def parser_lid_runner():
    config = load_config()

    extracted_pages_dir = Path(
        config["input"]["extracted_pages_dir"]
    )
    chunked_pages_dir = Path(
        config["output"]["chunked_pages_dir"]
    )

    chunked_pages_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    extracted_json_files = sorted(
        extracted_pages_dir.glob("*.json")
    )
    
    chunked_json_paths = []

    for extracted_json_path in extracted_json_files:
        output_path = initialize_chunked_json(
            extracted_json_path,
            chunked_pages_dir
        )
        chunked_json_paths.append(
            output_path
        )

    for chunked_json_path in chunked_json_paths:
        process_chunked_json(
            chunked_json_path
        )


if __name__ == "__main__":
    parser_lid_runner()