from pathlib import Path
import random
import yaml
import xml.etree.ElementTree as ET


XML_LANG = ("{http://www.w3.org/XML/1998/namespace}lang")


def load_config():
    with open("config/evaluator_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_tu_pair(element,src_lang,tgt_lang):
    languages = {}

    for tuv in element.findall("tuv"):
        lang = tuv.attrib.get(XML_LANG)
        seg = tuv.find("seg")
        if (lang and (seg is not None)):
            languages[lang] = (
                seg.text.strip()
                if seg.text
                else ""
            )

    if (src_lang not in languages or (tgt_lang not in languages)):
        return None

    return {
        "src": languages[src_lang],
        "tgt": languages[tgt_lang],
    }



def reservoir_sample_tmx(input_path,sample_size,seed,src_lang,tgt_lang):
    random.seed(seed)
    reservoir = []

    for event, elem in ET.iterparse(input_path,events=("end",)):
        if elem.tag == "tu":
            pair = extract_tu_pair(
                elem,
                src_lang,
                tgt_lang
            )
            if pair is not None:
                index = len(reservoir)
                if index < sample_size:
                    reservoir.append(pair)
                else:
                    replace_index = random.randint(0,index)
                    if replace_index < sample_size:
                        reservoir[replace_index] = pair
            elem.clear()

    return reservoir


def write_parallel_files(pairs,output_src_path,output_tgt_path):
    output_src_path = Path(output_src_path)
    output_tgt_path = Path(output_tgt_path)

    output_src_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_tgt_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with(
        open(output_src_path,"w",encoding="utf-8",newline="") as src_file,
        open(output_tgt_path,"w",encoding="utf-8",newline="") as tgt_file
    ): 
        for pair in pairs:
            src_file.write(
                pair["src"]
                .replace("\n", " ")
                +
                "\n"
            )
            tgt_file.write(
                pair["tgt"]
                .replace("\n", " ")
                +
                "\n"
            )


def sample_corpus(input_path,output_src_path,output_tgt_path,train_pairs):
    config = load_config()

    seed = config["sample_corpus_refer"]["random_seed"]
    src_lang = config["sample_corpus_refer"]["src_lang"]
    tgt_lang = config["sample_corpus_refer"]["tgt_lang"]

    sampled_pairs = reservoir_sample_tmx(
        input_path,
        train_pairs,
        seed,
        src_lang,
        tgt_lang
    )

    write_parallel_files(
        sampled_pairs,
        output_src_path,
        output_tgt_path
    )