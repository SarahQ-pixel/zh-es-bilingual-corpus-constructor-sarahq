import re
import yaml


URL_PATTERN = re.compile(
    r"(?i)\b(?:https?://|ftp://|www\.)\S+\b"
)


DOMAIN_PATTERN = re.compile(
    r"(?i)\b[\w.-]+\.(?:com|org|net|gov|edu|int|mil)(?:/\S*)?\b"
)


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


def load_config():
    with open("config/stati_filter_config.yaml","r",encoding="utf-8",) as f:
        return yaml.safe_load(f)


def contains_url(text):
    if URL_PATTERN.search(text):
        return True

    if DOMAIN_PATTERN.search(text):
        return True

    return False


def contains_email(text):
    if EMAIL_PATTERN.search(text):
        return True

    return False


def check_min_length(text, min_chars):
    text = text.strip()

    if len(text) <= min_chars:
        return False

    return True


def should_keep_pair(src_text, tgt_text, config):
    eliminator_config = config["pair_eliminator"]

    if eliminator_config["url"]["remove_url"]:
        if contains_url(src_text):
            return False, "url"
        if contains_url(tgt_text):
            return False, "url"


    if eliminator_config["email"]["remove_email"]:
        if contains_email(src_text):
            return False, "email"
        if contains_email(tgt_text):
            return False, "email"

    src_min_chars = eliminator_config["src"]["min_src_chars"]

    if not check_min_length(src_text,src_min_chars):
        return False, "src_length"

    tgt_min_chars = eliminator_config["tgt"]["min_tgt_chars"]

    if not check_min_length(tgt_text,tgt_min_chars):
        return False, "tgt_length"

    return True, None