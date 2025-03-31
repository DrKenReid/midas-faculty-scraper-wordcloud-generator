#!/usr/bin/env python3
"""
UMich Faculty Research Interests Scraper & Word Cloud Generator
================================================================

Overview:
---------
This asynchronous Python script scrapes research interests from the University of Michigan MIDAS
affiliated faculty pages, cleans the scraped text, and generates eight word clouds based on
different configurations. The data is gathered from two sources:
  1. Keywords (short descriptions) from the index pages.
  2. Full research descriptions from individual faculty pages.

The script is structured as follows:

1. **Constants and Setup**
   - Global constants are defined (e.g., CACHE_KEYWORDS, CACHE_DESCRIPTIONS, BASE_URL, etc.).
   - Logging is configured.
   - NLTK stopwords are downloaded, and custom common terms are loaded from a file.

2. **Scraping Functions**
   - `fetch_page(session, url, retries, delay)`: Fetches HTML content from a URL asynchronously with retry logic.
   - `scrape_keywords(session, verbose)`: Iterates over letters A–Z and paginates through each letter’s pages
     (using the &_paged parameter) until a "Nothing found." message is detected or no keyword paragraphs exist.
     Two nested progress bars show overall alphabetical progress and page-by-page progress for each letter.
   - `parse_faculty_links(html)`: Parses faculty profile links from an HTML page.
   - `scrape_descriptions_for_letter(session, letter)`: For a given letter, iterates over paginated pages to
     scrape full research descriptions from each faculty profile.
   - `scrape_all_descriptions(session)`: Iterates over letters A–Z to gather research descriptions.

3. **Cleaning Function**
   - `clean_text(text, remove_common_terms, remove_stop)`: Cleans the scraped text by converting it to lowercase,
     removing custom domain-specific terms, NLTK stopwords, and filtering out short words (less than 3 characters).

4. **Word Cloud Generation**
   - `generate_wordcloud(text, prefer_horizontal, dark_mode, filename)`: Generates and saves a word cloud image
     from the provided text, using the specified orientation (horizontal only or mixed) and color mode (dark/light).

5. **Main Asynchronous Function**
   - `main_async()`: Coordinates the entire workflow:
       a. Loads cached data (if available) or scrapes fresh data.
       b. Cleans the texts.
       c. Generates eight word clouds for each combination of:
          - Mode: dark/light
          - Orientation: horizontal-only (prefer_horizontal=1.0) and mixed (prefer_horizontal=0.5)
          - Data Source: keywords and descriptions.
       d. Displays summary tables with metrics and generated filenames.
       
6. **Script Entry Point**
   - `main()`: The main entry point that runs the asynchronous workflow using asyncio.

Usage:
------
Run the script as a standalone file:
    python <script_name>.py

Dependencies:
-------------
Ensure the following packages are installed:
    aiohttp, beautifulsoup4, nltk, wordcloud, tqdm, tabulate

Author:
-------
Ken Reid

License:
--------
MIT License
"""

import os
import re
import string
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
from tqdm import tqdm
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants and global variables
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
        session (aiohttp.ClientSession): The aiohttp client session.
        url (str): The URL to fetch.
        retries (int): Number of retries in case of failure.
        delay (float): Delay in seconds between retries.

    Returns:
        str: The HTML content as a string if successful; otherwise, an empty string.
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


async def scrape_keywords(session: aiohttp.ClientSession, verbose: bool = False) -> str:
    """
    Scrapes keywords (short descriptions) from all paginated A–Z pages.

    For each alphabetical letter, iterates over pages (using the &_paged
    parameter) until it finds a <p class="facetwp-no-results"> element whose text
    (case-insensitively) includes "nothing found" or until no keyword paragraphs are present.
    
    Two nested progress bars are displayed:
      - An outer bar for the alphabetical letters.
      - An inner bar for the pages processed for each letter.

    Args:
        session (aiohttp.ClientSession): The aiohttp client session.
        verbose (bool): If True, prints debug information.

    Returns:
        str: A single string containing all scraped keywords.
    """
    texts = []
    # Outer progress bar for alphabetical letters.
    for letter in tqdm(string.ascii_uppercase, desc="Alphabetical Letters", unit="letter"):
        page = 1
        # Inner progress bar for pages for this letter.
        with tqdm(desc=f"Letter {letter} pages", unit="page", leave=False) as page_bar:
            while True:
                url = f"{BASE_URL}?_last_name_a_z={letter}&_paged={page}"
                if verbose:
                    print(f"Fetching URL: {url}")
                html = await fetch_page(session, url)
                if not html:
                    if verbose:
                        print("No HTML returned, breaking.")
                    break

                soup = BeautifulSoup(html, "html.parser")
                no_results = soup.find("p", class_="facetwp-no-results")
                if no_results:
                    text_no = no_results.get_text(strip=True).lower()
                    if verbose:
                        print(f"Found no-results text: '{text_no}'")
                    if "nothing found" in text_no:
                        if verbose:
                            print(f"Stopping pagination for letter {letter} at page {page}")
                        break

                paragraphs = soup.find_all("p", class_="type-directory-subtitle")
                if not paragraphs:
                    if verbose:
                        print("No keyword paragraphs found, breaking.")
                    break

                for p in paragraphs:
                    txt = p.get_text(separator=" ", strip=True)
                    if txt:
                        texts.append(txt)

                page += 1
                page_bar.update(1)
    return " ".join(texts)


def parse_faculty_links(html: str) -> list:
    """
    Parses faculty profile links from the HTML content of a page.

    Args:
        html (str): The HTML content as a string.

    Returns:
        list: A list of URLs (strings) pointing to faculty profiles.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for h3 in soup.find_all("h3", class_=re.compile("type-directory-title")):
        a_tag = h3.find("a")
        if a_tag and a_tag.get("href"):
            links.append(a_tag["href"])
    return links


async def scrape_descriptions_for_letter(session: aiohttp.ClientSession, letter: str) -> str:
    """
    Scrapes research descriptions from all faculty profiles for a given letter, handling pagination.

    For each alphabetical letter, increments the page number until no faculty links are found.

    Args:
        session (aiohttp.ClientSession): The aiohttp client session.
        letter (str): The letter of the alphabet to filter faculty pages.

    Returns:
        str: A single string containing all research descriptions scraped for that letter.
    """
    collected = []
    page = 1
    while True:
        url = f"{BASE_URL}?_last_name_a_z={letter}&_paged={page}"
        html = await fetch_page(session, url)
        if not html:
            break
        faculty_links = parse_faculty_links(html)
        if not faculty_links:
            break
        for link in tqdm(faculty_links, desc=f"Scraping descriptions for {letter} page {page}", leave=False):
            page_html = await fetch_page(session, link)
            if page_html:
                soup = BeautifulSoup(page_html, "html.parser")
                container = soup.find(class_="dynamic-entry-content")
                if container:
                    text = container.get_text(separator=" ", strip=True)
                    collected.append(text)
                else:
                    logging.warning(f"'dynamic-entry-content' not found on {link}")
        page += 1
    return " ".join(collected)


async def scrape_all_descriptions(session: aiohttp.ClientSession) -> str:
    """
    Scrapes research descriptions from all paginated A–Z pages.

    Iterates through each alphabetical letter and retrieves research descriptions
    from all pages by incrementing the page number until no faculty links are found.

    Args:
        session (aiohttp.ClientSession): The aiohttp client session.

    Returns:
        str: A single string containing all research descriptions scraped.
    """
    texts = []
    for letter in tqdm(string.ascii_uppercase, desc="Scraping descriptions", unit="letter"):
        letter_text = await scrape_descriptions_for_letter(session, letter)
        texts.append(letter_text)
    return " ".join(texts)


# ---------------------------
# Cleaning Function
# ---------------------------
def clean_text(text: str, remove_common_terms: bool = True, remove_stop: bool = True) -> str:
    """
    Cleans the given text by converting it to lowercase, removing custom common terms,
    NLTK stopwords, and filtering out words with fewer than three characters.

    Args:
        text (str): The input text string.
        remove_common_terms (bool): Flag to remove domain-specific terms.
        remove_stop (bool): Flag to remove NLTK stopwords.

    Returns:
        str: The cleaned text as a single string.
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
def generate_wordcloud(text: str, prefer_horizontal: float, dark_mode: bool, filename: str) -> None:
    """
    Generates a word cloud image from the given text and saves it to a file.

    Args:
        text (str): The input text used for generating the word cloud.
        prefer_horizontal (float): The proportion of horizontal words (1.0 for horizontal only, 0.5 for mixed orientation).
        dark_mode (bool): Flag to determine background color (black for dark mode, white for light mode).
        filename (str): The output file path where the image will be saved.
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
    Main asynchronous function that orchestrates scraping, cleaning, word cloud generation,
    and displays a summary of the operations.
    
    Workflow:
      1. Load cached keywords and descriptions if available; otherwise, scrape fresh data.
      2. Clean the scraped texts.
      3. Generate word clouds for each combination of:
           - Mode: dark and light.
           - Orientation: horizontal-only (prefer_horizontal=1.0) and mixed (prefer_horizontal=0.5).
           - Source: keywords and descriptions.
      4. Print summary tables showing scraping metrics and generated image filenames.
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

    # Define configuration options:
    # For each mode (dark/light), orientation (horizontal/mixed), and source (keywords/descriptions)
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
                summary_files.append((mode_name, orientation_name, source_name,
                                      os.path.basename(filename)))

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
