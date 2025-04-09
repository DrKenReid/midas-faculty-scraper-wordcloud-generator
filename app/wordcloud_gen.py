"""
wordcloud_gen.py
----------------
Generates a word cloud image from a block of text using configuration options.
"""

import os
from wordcloud import WordCloud


def generate_wordcloud(text: str, prefer_horizontal: float, dark_mode: bool, filename: str) -> None:
    """
    Generate and save a word cloud image based on input text.

    Args:
        text (str): The input text for the word cloud.
        prefer_horizontal (float): Proportion of horizontal words (1.0 for horizontal only).
        dark_mode (bool): Set dark mode (black background) if True.
        filename (str): The output path for the saved image.
    """
    background_color = "black" if dark_mode else "white"
    wc = WordCloud(
        width=800,
        height=400,
        background_color=background_color,
        prefer_horizontal=prefer_horizontal,
        collocations=False,
        font_path="C:/Windows/Fonts/Arial.ttf"
    )
    wc.generate(text)
    wc.to_file(filename)
