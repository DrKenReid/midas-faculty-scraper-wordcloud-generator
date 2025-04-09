"""
main.py
-------
Entry point for the UMich Faculty Research Interests Scraper and Word Cloud Generator.

This script loads cached keyword and description data (or scrapes new data if needed),
cleans the text, generates word cloud images based on various configurations, and
prints a summary report.
"""

import os
import asyncio
import aiohttp
import logging
from tabulate import tabulate

from config import CACHE_KEYWORDS, CACHE_DESCRIPTIONS, OUTPUT_DIR
from keyword_scraper import scrape_keywords
from description_scraper import scrape_all_descriptions
from cleaning import clean_text
from wordcloud_gen import generate_wordcloud


async def main_async() -> None:
    """
    Orchestrate scraping, cleaning, word cloud generation, and summary reporting.
    """
    # Load or scrape keywords.
    if os.path.exists(CACHE_KEYWORDS):
        with open(CACHE_KEYWORDS, "r", encoding="utf-8") as f:
            keywords_text = f.read()
        logging.info("Loaded keywords from cache.")
    else:
        async with aiohttp.ClientSession() as session:
            keywords_text = await scrape_keywords(session)
        with open(CACHE_KEYWORDS, "w", encoding="utf-8") as f:
            f.write(keywords_text)
        logging.info("Saved keywords to cache.")

    # Load or scrape descriptions.
    if os.path.exists(CACHE_DESCRIPTIONS):
        with open(CACHE_DESCRIPTIONS, "r", encoding="utf-8") as f:
            descriptions_text = f.read()
        logging.info("Loaded descriptions from cache.")
    else:
        async with aiohttp.ClientSession() as session:
            descriptions_text = await scrape_all_descriptions(session)
        with open(CACHE_DESCRIPTIONS, "w", encoding="utf-8") as f:
            f.write(descriptions_text)
        logging.info("Saved descriptions to cache.")

    # Clean the texts.
    cleaned_keywords = clean_text(keywords_text)
    cleaned_descriptions = clean_text(descriptions_text)
    keywords_word_count = len(cleaned_keywords.split())
    descriptions_word_count = len(cleaned_descriptions.split())

    # Define configurations for word cloud generation.
    modes = [(True, "dark"), (False, "light")]
    orientations = [("horizontal", 1.0), ("mixed", 0.5)]
    sources = [("keywords", cleaned_keywords), ("descriptions", cleaned_descriptions)]
    summary_files = []

    # Generate word clouds for all configuration combinations.
    for dark_mode, mode_name in modes:
        for orientation_name, prefer_horizontal in orientations:
            for source_name, text_content in sources:
                filename = os.path.join(OUTPUT_DIR, f"{source_name}_{orientation_name}_{mode_name}.png")
                generate_wordcloud(text_content, prefer_horizontal, dark_mode, filename)
                summary_files.append((mode_name, orientation_name, source_name, os.path.basename(filename)))

    # Print a summary table of scraping metrics.
    summary_data = [
        ["Keywords pages scraped", 26],
        ["Description pages scraped", "26 (letters) + individual faculty links"],
        ["Total words (keywords)", keywords_word_count],
        ["Total words (descriptions)", descriptions_word_count]
    ]
    summary_table = tabulate(summary_data, headers=["Metric", "Value"], tablefmt="fancy_grid")
    print(summary_table)

    # Print a summary table of generated word cloud images.
    images_table = tabulate(
        summary_files,
        headers=["Mode", "Orientation", "Source", "Filename"],
        tablefmt="fancy_grid"
    )
    print(f"\nWordCloud Images Saved in '{OUTPUT_DIR}':")
    print(images_table)


def main() -> None:
    """
    Start the asynchronous scraping and word cloud generation process.
    """
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
