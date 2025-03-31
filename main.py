#!/usr/bin/env python3
"""
UMich Faculty Research Interests Scraper & Word Cloud Generator

This asynchronous Python script scrapes research interests from the University of
Michigan affiliated faculty pages, cleans the text, and generates eight word clouds.
For each light/dark mode, two word clouds are generated for horizontal-only orientation
and two for mixed orientation, with one word cloud using keywords and one using
descriptions. A summary table is then printed using the tabulate library.
"""

import os
import re
import string
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import matplotlib.pyplot as plt  # Imported for potential display purposes
import nltk
from nltk.corpus import stopwords
from tqdm import tqdm
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
CACHE_KEYWORDS = "keywords.txt"
CACHE_DESCRIPTIONS = "descriptions.txt"
COMMON_TERMS_FILE = "removed_words.txt"
OUTPUT_DIR = "output"
BASE_URL = "https://midas.umich.edu/people/affiliated-faculty/"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Download NLTK stopwords if not already available
nltk.download("stopwords", quiet=True)
STOP_WORDS = set(stopwords.words("english"))

# Load common DS-related terms from file
if os.path.exists(COMMON_TERMS_FILE):
    with open(COMMON_TERMS_FILE, "r", encoding="utf-8") as f:
        REMOVED_TERMS = [line.strip() for line in f if line.strip()]
else:
    REMOVED_TERMS = []


# ---------------------------
# Scraping Functions
# ---------------------------
async def fetch_page(session: aiohttp.ClientSession, url: str,
                     retries: int = 3, delay: float = 1) -> str:
    """
    Asynchronously fetches the HTML content of the given URL with retry logic.

    Args:
        session: The aiohttp client session.
        url: The URL to fetch.
        retries: Number of retries in case of failure.
        delay: Delay in seconds between retries.

    Returns:
        The HTML content as a string if successful; otherwise, an empty string.
    """
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logging.warning(
                f"Error fetching {url}: {e} (attempt {attempt+1}/{retries})"
            )
            await asyncio.sleep(delay)
    logging.error(f"Failed to fetch {url} after {retries} attempts.")
    return ""


async def scrape_keywords(session: aiohttp.ClientSession) -> str:
    """
    Scrapes keywords (short descriptions) from A-Z pages.

    Args:
        session: The aiohttp client session.

    Returns:
        A single string containing all scraped keywords.
    """
    texts = []
    for letter in tqdm(string.ascii_uppercase, desc="Scraping keywords",
                       unit="letter"):
        url = f"{BASE_URL}?_last_name_a_z={letter}"
        html = await fetch_page(session, url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            paragraphs = soup.find_all("p", class_=re.compile("type-directory-subtitle"))
            for p in paragraphs:
                text = p.get_text(separator=" ", strip=True)
                if text:
                    texts.append(text)
        else:
            logging.warning(f"No content for letter {letter}")
    return " ".join(texts)


def parse_faculty_links(html: str) -> list:
    """
    Parses faculty profile links from the HTML content of a page.

    Args:
        html: The HTML content as a string.

    Returns:
        A list of URLs (strings) pointing to faculty profiles.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for h3 in soup.find_all("h3", class_=re.compile("type-directory-title")):
        a_tag = h3.find("a")
        if a_tag and a_tag.get("href"):
            links.append(a_tag["href"])
    return links


async def scrape_descriptions_for_letter(session: aiohttp.ClientSession,
                                         letter: str) -> str:
    """
    Scrapes research descriptions from all faculty profiles for a given letter.

    Args:
        session: The aiohttp client session.
        letter: The letter of the alphabet to filter faculty pages.

    Returns:
        A single string containing all research descriptions scraped for that letter.
    """
    collected = []
    url = f"{BASE_URL}?_last_name_a_z={letter}"
    html = await fetch_page(session, url)
    if html:
        faculty_links = parse_faculty_links(html)
        for link in tqdm(faculty_links,
                         desc=f"Scraping descriptions for {letter}",
                         leave=False):
            page_html = await fetch_page(session, link)
            if page_html:
                soup = BeautifulSoup(page_html, "html.parser")
                container = soup.find(class_="dynamic-entry-content")
                if container:
                    text = container.get_text(separator=" ", strip=True)
                    collected.append(text)
                else:
                    logging.warning(f"'dynamic-entry-content' not found on {link}")
    return " ".join(collected)


async def scrape_all_descriptions(session: aiohttp.ClientSession) -> str:
    """
    Scrapes research descriptions from all A-Z pages.

    Args:
        session: The aiohttp client session.

    Returns:
        A single string containing all research descriptions scraped.
    """
    texts = []
    for letter in tqdm(string.ascii_uppercase, desc="Scraping descriptions",
                       unit="letter"):
        letter_text = await scrape_descriptions_for_letter(session, letter)
        texts.append(letter_text)
    return " ".join(texts)


# ---------------------------
# Cleaning Function
# ---------------------------
def clean_text(text: str, remove_common_terms: bool = True,
               remove_stop: bool = True) -> str:
    """
    Cleans the given text by converting it to lowercase, removing common terms,
    stopwords, and filtering out words with fewer than three characters.

    Args:
        text: The input text string.
        remove_common_terms: Flag to remove domain-specific terms.
        remove_stop: Flag to remove NLTK stopwords.

    Returns:
        The cleaned text as a single string.
    """
    text = text.lower()
    if remove_common_terms:
        for term in REMOVED_TERMS:
            text = re.sub(re.escape(term), "", text, flags=re.IGNORECASE)
    words = re.findall(r'\w+', text)
    filtered_words = [
        word for word in words
        if len(word) >= 3 and (word not in STOP_WORDS if remove_stop else True)
    ]
    return " ".join(filtered_words)


# ---------------------------
# WordCloud Generation Function
# ---------------------------
def generate_wordcloud(text: str, prefer_horizontal: float, dark_mode: bool,
                       filename: str) -> None:
    """
    Generates a word cloud image from the given text and saves it to a file.

    Args:
        text: The input text used for generating the word cloud.
        prefer_horizontal: The proportion of horizontal words.
        dark_mode: Flag to determine background color (black for dark mode).
        filename: The output file path where the image will be saved.
    """
    background_color = "black" if dark_mode else "white"
    wc = WordCloud(width=800, height=400, background_color=background_color,
                   prefer_horizontal=prefer_horizontal, collocations=False)
    wc.generate(text)
    wc.to_file(filename)


# ---------------------------
# Main Asynchronous Function
# ---------------------------
async def main_async() -> None:
    """
    Main asynchronous function that orchestrates scraping, cleaning, word cloud
    generation, and displays a summary of the operations.
    """
    # Load or scrape keywords
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

    # Load or scrape descriptions
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

    # Clean texts separately
    cleaned_keywords = clean_text(keywords_text)
    cleaned_descriptions = clean_text(descriptions_text)
    keywords_word_count = len(cleaned_keywords.split())
    descriptions_word_count = len(cleaned_descriptions.split())

    # Define configuration options
    # For orientation: 'horizontal' (prefer_horizontal=1.0) or 'mixed' (prefer_horizontal=0.5)
    modes = [(True, "dark"), (False, "light")]
    orientations = [("horizontal", 1.0), ("mixed", 0.5)]
    sources = [("keywords", cleaned_keywords), ("descriptions", cleaned_descriptions)]

    summary_files = []  # To hold summary information for generated images

    # Generate 8 word clouds based on mode, orientation, and source
    for dark_mode, mode_name in modes:
        for orientation_name, prefer_horizontal in orientations:
            for source_name, text_content in sources:
                filename = os.path.join(
                    OUTPUT_DIR, f"{source_name}_{orientation_name}_{mode_name}.png"
                )
                generate_wordcloud(text_content, prefer_horizontal, dark_mode, filename)
                summary_files.append((mode_name, orientation_name, source_name, os.path.basename(filename)))

    # Print a summary of scraping results
    summary_data = [
        ["Keywords pages scraped", 26],
        ["Description pages scraped", "26 (letters) + individual faculty links"],
        ["Total words (keywords)", keywords_word_count],
        ["Total words (descriptions)", descriptions_word_count]
    ]
    summary_table = tabulate(summary_data, headers=["Metric", "Value"],
                             tablefmt="fancy_grid")
    print(summary_table)

    # Print a summary table for the generated word cloud images
    images_table = tabulate(
        summary_files,
        headers=["Mode", "Orientation", "Source", "Filename"],
        tablefmt="fancy_grid"
    )
    print(f"\nWordCloud Images Saved in '{OUTPUT_DIR}':")
    print(images_table)


def main() -> None:
    """
    Main entry point for the script.
    """
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
