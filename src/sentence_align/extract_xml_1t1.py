from pathlib import Path
import yaml
import xml.etree.ElementTree as ET


def load_config():
    with open("config/sentence_align_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_xml(xml_path):
    xml_path = Path(xml_path)

    tree = ET.parse(xml_path)

    return tree.getroot()


def get_doc_language(root, config):
    lang_tag = config["extract_xml_1t1"]["language_tag"]
    ident_attr = config["extract_xml_1t1"]["language_ident_attr"]

    for elem in root.iter():
        if elem.tag.endswith(lang_tag):
            return elem.attrib.get(ident_attr, "")
    return ""


def extract_sentences_by_lang(root, target_lang, config):
    xpath = config["extract_xml_1t1"]["sentence_xpath"]
    lang_attr = config["extract_xml_1t1"]["lang_attr"]
    id_attr = config["extract_xml_1t1"]["sentence_id_attr"]

    sentences_li = []
    corresp = []

    nodes = root.findall(xpath)

    for idx, node in enumerate(nodes):
        lang = node.attrib.get(lang_attr, "")
        if lang != target_lang:
            continue

        text = "".join(node.itertext()).strip()
        sid = node.attrib.get(id_attr, "")
        sentences_li.append(text)
        corresp.append((len(sentences_li)-1, sid))

    return sentences_li, corresp


def extract_xml(zh_xml_path, es_xml_path):
    config = load_config()

    zh_root = load_xml(zh_xml_path)
    es_root = load_xml(es_xml_path)

    zh_doc_lang = get_doc_language(zh_root, config)
    es_doc_lang = get_doc_language(es_root, config)

    if zh_doc_lang != config["extract_xml_1t1"]["zh_lang_ident"]:
        raise ValueError("ZH XML language ident mismatch")

    if es_doc_lang != config["extract_xml_1t1"]["es_lang_ident"]:
        raise ValueError("ES XML language ident mismatch")

    zh_sentences_li, zh_corresp = extract_sentences_by_lang(
        zh_root,
        config["extract_xml_1t1"]["zh_lang_ident"],
        config
    )

    es_sentences_li, es_corresp = extract_sentences_by_lang(
        es_root,
        config["extract_xml_1t1"]["es_lang_ident"],
        config
    )

    return zh_sentences_li, zh_corresp, es_sentences_li, es_corresp