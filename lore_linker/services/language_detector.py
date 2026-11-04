from langdetect import detect, LangDetectException, DetectorFactory

DetectorFactory.seed = 0

def detect_language(text):
    """
    Detect the dominant language of the supplied text.

    Returns a language code such as 'en' or 'ja'.
    Returns None when the text cannot be detected.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    try:
        return detect(text)
    except LangDetectException:
        return None

def classify_language(text):
    """
    Classify whether a story is eligible for English text analysis.

    Returns:
        (language_status, language_reason)
    """
    if not isinstance(text, str) or not text.strip():
        return "excluded", "Story body is empty."

    try:
        from langdetect import detect_langs

        language_results = detect_langs(text)
    except LangDetectException:
        return "excluded", "Language could not be detected."

    if not language_results:
        return "excluded", "Language could not be detected."

    english_probability = next(
        (
            result.prob
            for result in language_results
            if result.lang == "en"
        ),
        0.0,
    )

    if english_probability >= 0.7:
        return "accepted", None

    detected_language = language_results[0].lang

    return (
        "excluded",
        f"English probability is too low. Detected language: {detected_language}.",
    )
