# Language Identification for Web Pages (LID) with Analysis of URL Segments
import json
from pathlib import Path
import yaml


def load_config():
    config_path = Path("config/parser_lid_config.yaml")
    with open(config_path,"r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def iden_url(chunked_page_path):
    config = load_config()

    language_markers = (config["lid_url"]["language_markers"])

    case_sensitive = (config["lid_url"]["case_sensitive"])

    with open(chunked_page_path,"r",encoding="utf-8") as f:
        page_data = json.load(f)

    url_segments = page_data.get(
        "url_segments",
        []
    )

    if not case_sensitive:
        url_segments = [
            segment.lower()
            for segment in url_segments
            if isinstance(segment, str)
        ]

    detected_language = None

    for language_code, markers in (language_markers.items()):
        if not case_sensitive:
            markers = [
                marker.lower()
                for marker in markers
            ]
        for marker in markers:
            if marker in url_segments:
                detected_language = (
                    language_code
                )
                break
        if detected_language is not None:
            break

    if detected_language is not None:
        page_data["language"] = (detected_language)
        page_data["language_source"] = ("url")
        page_data["stage_origin"] = ("url")

        with open(chunked_page_path,"w",encoding="utf-8") as f:
            json.dump(
                page_data,
                f,
                ensure_ascii=False,
                indent=2
            )