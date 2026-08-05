import json
from pathlib import Path
import yaml
from lxml import html


def load_config():
    config_path = Path("config/parser_lid_config.yaml")
    with open(config_path,"r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_depth(element):
    depth = 0
    parent = element.getparent()
    while parent is not None:
        depth += 1
        parent = parent.getparent()
    return depth


def clean_dom(tree, ignored_tags):
    for tag in ignored_tags:
        for node in tree.xpath(f"//{tag}"):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)


def extract_info(chunked_page_path):
    config = load_config()

    content_tags = config["lxml_parser"]["content_tags"]
    structure_tags = config["lxml_parser"]["structure_tags"]
    ignored_tags = config["lxml_parser"]["ignored_tags"]
    min_text_length = config["lxml_parser"]["min_text_length"]

    with open(chunked_page_path,"r",encoding="utf-8") as f:
        page_data = json.load(f)

    html_path = page_data["rendered_html_path"]

    with open(html_path,"rb") as f:
        html_content = f.read()

    tree = html.fromstring(html_content)

    clean_dom(tree, ignored_tags)

    chunks = []
    text_blocks = []
    chunk_index = 0
    text_index = 0

    for element in tree.iter():
        tag = element.tag

        if not isinstance(
            tag,
            str
        ):
            continue

        tag = tag.lower()

        if tag in ignored_tags:
            continue

        dom_path = tree.getroottree().getpath(element)

        depth = get_depth(element)

        if tag in content_tags:
            text = element.text_content()
            text = " ".join(
                text.split()
            )
            if len(text) < min_text_length:
                continue
            
            text_blocks.append(text)

            chunks.append(
                {
                    "chunk_id": f"chunk_{chunk_index}",
                    "tag": tag,
                    "dom_path": dom_path,
                    "depth": depth,
                    "is_content": True,
                    "text_id": text_index,
                    "text_length": len(text)
                }
            )
            chunk_index += 1
            text_index += 1

        elif tag in structure_tags:
            chunks.append(
                {
                    "chunk_id":  f"chunk_{chunk_index}",
                    "tag": tag,
                    "dom_path": dom_path,
                    "depth": depth,
                    "is_content": False,
                    "text_id": None,
                    "text_length": None
                }
            )
            chunk_index += 1

    page_data["chunks"] = chunks
    page_data["text"] = text_blocks
    page_data["stage_origin"] = "lxml"

    with open(chunked_page_path,"w",encoding="utf-8") as f:
        json.dump(
            page_data,
            f,
            ensure_ascii=False,
            indent=2
        )