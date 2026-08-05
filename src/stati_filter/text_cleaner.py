import html
import re
import yaml


CSS_PATTERN = re.compile(
    r"<style\b[^>]*>.*?</style>",
    flags=re.IGNORECASE | re.DOTALL,
)


JAVASCRIPT_PATTERN = re.compile(
    r"<script\b[^>]*>.*?</script>",
    flags=re.IGNORECASE | re.DOTALL,
)


HTML_PATTERN = re.compile(
    r"<[^>]+>",
    flags=re.IGNORECASE,
)


MULTIPLE_WHITESPACE_PATTERN = re.compile(
    r"\s+"
)


def load_config():
    with open("config/stati_filter_config.yaml","r",encoding="utf-8",) as f:
        return yaml.safe_load(f)


def remove_css(text):
    new_text = CSS_PATTERN.sub("",text)

    changed = new_text != text

    return new_text, changed


def remove_javascript(text):
    new_text = JAVASCRIPT_PATTERN.sub("",text)

    changed = new_text != text

    return new_text, changed


def remove_html(text):
    new_text = HTML_PATTERN.sub("",text)

    changed = new_text != text

    return new_text, changed


def normalize_whitespace(text):
    text = html.unescape(text)
    
    text = text.replace("\u00A0"," ")

    text = MULTIPLE_WHITESPACE_PATTERN.sub(" ",text)

    return text.strip()


def clean_text(text, config):
    cleaner_config = config["text_cleaner"]

    stats = {
        "css_removed": False,
        "javascript_removed": False,
        "html_removed": False,
        "whitespace_normalized": False,
    }

    original_text = text


    if cleaner_config["css"]["remove_css"]:
        text, changed = remove_css(text)

        if changed:
            stats["css_removed"] = True


    if cleaner_config["javascript"]["remove_javascript"]:
        text, changed = remove_javascript(text)

        if changed:
            stats["javascript_removed"] = True


    if cleaner_config["html"]["remove_html"]:
        text, changed = remove_html(text)

        if changed:
            stats["html_removed"] = True


    if cleaner_config["whitespace"]["normalize_whitespace"]:
        normalized_text = normalize_whitespace(text)

        if normalized_text != text:
            stats["whitespace_normalized"] = True

        text = normalized_text


    if text != original_text:
        text = text.strip()


    return text, stats