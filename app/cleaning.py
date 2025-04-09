"""
cleaning.py
-----------
Provides a function to clean scraped text by removing custom domain-specific terms,
NLTK stopwords, and extraneous characters. The function converts text to lowercase,
removes only whole occurrences of the specified common terms (using word boundaries),
tokenizes the text, and discards words shorter than three characters.
"""

import re
from config import REMOVED_TERMS, STOP_WORDS


def clean_text(text: str, remove_common_terms: bool = True, remove_stop: bool = True) -> str:
    """
    Clean the input text by converting it to lowercase, removing domain-specific terms
    (only if they appear as whole words), removing NLTK stopwords if enabled, and discarding
    words shorter than three characters.

    This function performs the following tasks:
      1. Converts the input text to lowercase.
      2. Optionally removes custom domain-specific terms:
         - Each term is removed only when it appears as a whole word using regular expression
           word boundaries. This prevents accidental removal of parts of other words.
      3. Tokenizes the text into words by matching alphanumeric sequences.
      4. Filters out words that are shorter than three characters and, if enabled, removes NLTK
         stopwords.

    Args:
        text (str): The raw text to clean.
        remove_common_terms (bool): If True, removes custom domain-specific terms defined in REMOVED_TERMS.
        remove_stop (bool): If True, removes NLTK stopwords defined in STOP_WORDS.

    Returns:
        str: The cleaned text composed of filtered words separated by a single space.
    """
    # Convert the text to lowercase.
    text = text.lower()

    # Remove each custom domain-specific term only if it appears as a whole word.
    if remove_common_terms:
        for term in REMOVED_TERMS:
            # Build a pattern to match the term as a whole word, using word boundaries (\b).
            pattern = r"\b" + re.escape(term) + r"\b"
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Tokenize the text into words, selecting only alphanumeric characters.
    words = re.findall(r'\w+', text)

    # Filter out words that are shorter than three characters and, optionally, any stopwords.
    filtered_words = [
        word for word in words
        if len(word) >= 3 and (word not in STOP_WORDS if remove_stop else True)
    ]

    # Return the cleaned words joined by a single space.
    return " ".join(filtered_words)
