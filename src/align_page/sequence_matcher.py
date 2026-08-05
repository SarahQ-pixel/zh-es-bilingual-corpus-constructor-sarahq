from difflib import SequenceMatcher


def _extract_sequence(page: dict):

    sequence = []

    for chunk in page.get("chunks", []):
        tag = chunk.get("tag", "none")
        depth = chunk.get("depth", -1)
        is_content = chunk.get("is_content", False)
        content_flag = "TR" if is_content else "FA"

        token = f"{tag}_{depth}_{content_flag}"
        sequence.append(token)

    return sequence


def sequence_matcher_sim_cal(zh_page, es_page):

    zh_seq = _extract_sequence(zh_page)
    es_seq = _extract_sequence(es_page)

    if not zh_seq or not es_seq:
        return 0.0

    matcher = SequenceMatcher(None, zh_seq, es_seq)

    similarity = matcher.ratio()

    return float(similarity)