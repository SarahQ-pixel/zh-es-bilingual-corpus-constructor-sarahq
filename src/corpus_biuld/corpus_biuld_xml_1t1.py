from pathlib import Path
import yaml
import xml.etree.ElementTree as ET


def load_config():
    with open("config/corpus_biuld_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_xml(xml_path):
    xml_path = Path(xml_path)

    tree = ET.parse(xml_path)

    return tree.getroot()


def get_doc_language(root, config):
    lang_tag = config["corpus_biuld_xml_1t1"]["language_tag"]
    ident_attr = config["corpus_biuld_xml_1t1"]["language_ident_attr"]

    for elem in root.iter():
        if elem.tag.endswith(lang_tag):
            return elem.attrib.get(
                ident_attr,
                ""
            )

    return ""


def build_sentence_lookup(root,target_lang,config):
    xpath = config["corpus_biuld_xml_1t1"]["sentence_xpath"]
    lang_attr = config["corpus_biuld_xml_1t1"]["lang_attr"]
    id_attr = config["corpus_biuld_xml_1t1"]["sentence_id_attr"]

    sentence_lookup = {}

    nodes = root.findall(xpath)

    for node in nodes:
        lang = node.attrib.get(lang_attr,"")
        if lang != target_lang:
            continue
        sentence_id = node.attrib.get(id_attr,"")
        text = "".join(
            node.itertext()
        ).strip()
        sentence_lookup[sentence_id] = text

    return sentence_lookup


def load_document(xml_path):
    config = load_config()

    root = load_xml(xml_path)

    document_language = get_doc_language(root,config)

    if (document_language == config["corpus_biuld_xml_1t1"]["zh_lang_ident"]):
        target_lang = config["corpus_biuld_xml_1t1"]["zh_lang_ident"]

    elif (document_language == config["corpus_biuld_xml_1t1"]["es_lang_ident"]):
        target_lang = config["corpus_biuld_xml_1t1"]["es_lang_ident"]

    else:
        raise ValueError(
            f"Unsupported document language: "
            f"{document_language}"
        )

    return build_sentence_lookup(root,target_lang,config)


def get_sentence(document,sentence_id,language):
    if sentence_id not in document:
        raise KeyError(
            f"Sentence '{sentence_id}' not found."
        )

    return document[sentence_id]