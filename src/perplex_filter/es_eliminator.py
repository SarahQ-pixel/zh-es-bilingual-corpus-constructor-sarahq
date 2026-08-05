import yaml

from src.perplex_filter.perplex_cal import calculate_perplexity


def load_config():
    with open("config/perplex_filter_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_threshold(text):
    config = load_config()

    text_length = len(text)

    short = config["es_eliminator"]["thresholds"]["short"]
    medium = config["es_eliminator"]["thresholds"]["medium"]
    long = config["es_eliminator"]["thresholds"]["long"]

    if (
        short.get("enable", False)
        and medium.get("enable", False)
        and short["max_length"] > medium["max_length"]
    ):
        raise ValueError(
            "Invalid threshold configuration: "
            "short max_length cannot be greater than medium max_length."
        )

    if (
        short.get("enable", False)
        and text_length <= short["max_length"]
    ):
        return (
            short["threshold"],
            "short",
        )

    if (
        medium.get("enable", False)
        and text_length <= medium["max_length"]
    ):
        return (
            medium["threshold"],
            "medium",
        )

    return (
        long["threshold"],
        "long",
    )


def eliminate(text,model,tokenizer,score_type):
    score = calculate_perplexity(
        text,
        model,
        tokenizer,
        score_type,
    )

    threshold, threshold_type = get_threshold(text)

    should_eliminate = score > threshold

    debug_information = {
        "score": score,
        "threshold": threshold,
        "threshold_type": threshold_type,
        "text": text,
    }

    return should_eliminate, debug_information