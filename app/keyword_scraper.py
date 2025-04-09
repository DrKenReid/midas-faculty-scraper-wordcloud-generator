"""
keyword_scraper.py
------------------
Contains the asynchronous function to scrape keywords (short descriptions)
from the paginated A–Z faculty pages.
"""

import string
from tqdm import tqdm
from bs4 import BeautifulSoup
from config import BASE_URL
from utils import fetch_page

# Base URL remains defined in config.py; if not already present, add below.
BASE_URL = "https://midas.umich.edu/people/affiliated-faculty/"


async def scrape_keywords(session, verbose: bool = False) -> str:
    """
    Scrape keywords from paginated A–Z pages.

    For each alphabetical letter, pages are fetched until a "nothing found" message
    or absence of keyword paragraphs is detected.

    Args:
        session (aiohttp.ClientSession): The active HTTP session.
        verbose (bool): If True, prints debug information.

    Returns:
        str: A single string of concatenated keywords.
    """
    texts = []
    for letter in tqdm(string.ascii_uppercase, desc="Alphabetical Letters", unit="letter"):
        page = 1
        with tqdm(desc=f"Letter {letter} pages", unit="page", leave=False) as page_bar:
            while True:
                url = f"{BASE_URL}?_last_name_a_z={letter}&_paged={page}"
                if verbose:
                    print(f"Fetching URL: {url}")
                html = await fetch_page(session, url)
                if not html:
                    break
                soup = BeautifulSoup(html, "html.parser")
                no_results = soup.find("p", class_="facetwp-no-results")
                if no_results and "nothing found" in no_results.get_text(strip=True).lower():
                    break
                paragraphs = soup.find_all("p", class_="type-directory-subtitle")
                if not paragraphs:
                    break
                for p in paragraphs:
                    txt = p.get_text(separator=" ", strip=True)
                    if txt:
                        texts.append(txt)
                page += 1
                page_bar.update(1)
    return " ".join(texts)
