import langid


def eliminate(text):
    detected_lang, confidence = (
        langid.classify(text)
    )

    should_eliminate = (
        detected_lang != "es"
    )

    debug_information = {
        "text": text,
        "detected_language": detected_lang,
        "confidence": confidence,
        "expected_language": "es",
    }

    return should_eliminate, debug_information