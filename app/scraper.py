"""
scraper.py
----------
Contains asynchronous functions for scraping keyword and description data from
UMich MIDAS affiliated faculty pages.
"""

import asyncio
import string
import re
import logging
import aiohttp
from tqdm import tqdm
from bs4 import BeautifulSoup
from config import BASE_URL


async def fetch_page(session: aiohttp.ClientSession, url: str,
                     retries: int = 3, delay: float = 1) -> str:
    """
    Fetch the HTML content for a URL using asynchronous requests with retry logic.

    Args:
        session (aiohttp.ClientSession): The active session.
        url (str): The URL to fetch.
        retries (int): Number of retry attempts.
        delay (float): Seconds to wait between retries.

    Returns:
        str: HTML content if successful; otherwise, an empty string.
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
    Scrape keywords (short descriptions) from paginated A–Z pages.

    Args:
        session (aiohttp.ClientSession): The aiohttp session.
        verbose (bool): If True, prints debug information.

    Returns:
        str: All keywords concatenated into a single string.
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
                if no_results:
                    if "nothing found" in no_results.get_text(strip=True).lower():
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


def parse_faculty_links(html: str) -> list:
    """
    Parse and return a list of faculty profile URLs from the given HTML.

    Args:
        html (str): HTML content to parse.

    Returns:
        list: A list of URLs (strings) for faculty profiles.
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
    Scrape research descriptions for a given alphabet letter.

    Args:
        session (aiohttp.ClientSession): The aiohttp session.
        letter (str): The alphabet letter to use for filtering.

    Returns:
        str: All research descriptions for the letter concatenated.
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
                    collected.append(container.get_text(separator=" ", strip=True))
                else:
                    logging.warning(f"'dynamic-entry-content' not found on {link}")
        page += 1
    return " ".join(collected)


async def scrape_all_descriptions(session: aiohttp.ClientSession) -> str:
    """
    Iterate through A–Z pages and scrape all research descriptions.

    Args:
        session (aiohttp.ClientSession): The aiohttp session.

    Returns:
        str: All concatenated research descriptions.
    """
    texts = []
    for letter in tqdm(string.ascii_uppercase, desc="Scraping descriptions", unit="letter"):
        letter_text = await scrape_descriptions_for_letter(session, letter)
        texts.append(letter_text)
    return " ".join(texts)
