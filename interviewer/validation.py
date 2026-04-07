import re


# This small list contains rude or inappropriate words that
# should not be accepted as valid interview answers.
# The goal is not to build perfect moderation, just to catch
# obvious cases and keep the interaction professional.
BAD_WORDS = {
    "idiot", "stupid", "moron", "dumb", "fuck", "shit", "bitch", "asshole"
}


def tokenize_words(text: str) -> list[str]:
    """
    Extract normal-looking words from text.

    We convert the text to lowercase first so comparisons are easier later.
    The regular expression keeps alphabetic words and words with apostrophes.
    """
    return re.findall(r"[A-Za-z']+", text.lower())


def is_repeated_character_junk(text: str) -> bool:
    """
    Catch things like:
    - aaaaaa
    - !!!!!!
    - 111111

    These are treated as invalid because they do not look like
    real interview answers.
    """
    # Remove spaces so something like "a a a a" is still caught.
    compact = re.sub(r"\s+", "", text.lower())

    # If the text is long enough and contains only one unique character,
    # it is most likely junk input.
    return len(compact) >= 4 and len(set(compact)) == 1


def contains_rude_language(text: str) -> bool:
    """
    Check if the text contains rude or inappropriate words.

    We split the answer into words and compare them against the BAD_WORDS list.
    """
    words = set(tokenize_words(text))
    return any(word in BAD_WORDS for word in words)


def looks_like_gibberish(text: str) -> bool:
    """
    Very simple gibberish check.

    We only want to reject clearly bad input, not real answers with typos.
    This function is intentionally simple so the app stays fast and does not
    wrongly reject honest answers too often.
    """
    clean = text.strip()

    # Empty answers or answers with only spaces are not valid.
    if not clean:
        return True

    # If the answer has no letters or numbers at all, it is not useful.
    if not re.search(r"[A-Za-z0-9]", clean):
        return True

    # Reject repeated junk like "aaaaaa" or "!!!!!!".
    if is_repeated_character_junk(clean):
        return True

    words = tokenize_words(clean)

    # No words at all is not acceptable.
    if not words:
        return True

    # Very short random-looking answers should be rejected.
    # Example: "aa" or "???" or "jk"
    if len(words) <= 2 and len(clean) < 8:
        return True

    return False


def validate_answer(text: str) -> tuple[bool, str]:
    """
    Validate a candidate answer.

    Return:
    - True, "" if the answer is valid
    - False, message if the answer should be rejected

    This is the main function used by the app before allowing
    the user to move to the next question.
    """
    clean = text.strip()

    # Block empty answers first.
    if not clean:
        return False, "Please answer the question before continuing."

    # Block rude language so the app stays professional.
    if contains_rude_language(clean):
        return False, "Please avoid inappropriate language and answer the question professionally."

    # Block answers that look too incomplete or unclear.
    if looks_like_gibberish(clean):
        return False, "Your answer does not look complete or clear. Please write a proper answer."

    # If none of the checks failed, the answer is accepted.
    return True, ""
