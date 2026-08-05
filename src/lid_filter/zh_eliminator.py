import langid


def eliminate(text):
    detected_lang, confidence = (
        langid.classify(text)
    )

    should_eliminate = (
        detected_lang != "zh"
    )

    debug_information = {
        "text": text,
        "detected_language": detected_lang,
        "confidence": confidence,
        "expected_language": "zh",
    }

    return should_eliminate, debug_information