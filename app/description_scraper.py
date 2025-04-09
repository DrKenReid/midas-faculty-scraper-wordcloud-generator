"""
description_scraper.py
----------------------
Contains functions for parsing faculty links and scraping research descriptions
from faculty profile pages.
"""

import re
import string
from tqdm import tqdm
from bs4 import BeautifulSoup
from config import BASE_URL
from utils import fetch_page

# Ensure BASE_URL is available
BASE_URL = "https://midas.umich.edu/people/affiliated-faculty/"


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


async def scrape_descriptions_for_letter(session, letter: str) -> str:
    """
    Scrape research descriptions for a given alphabetical letter.

    Args:
        session (aiohttp.ClientSession): The active HTTP session.
        letter (str): The alphabetical letter to filter results.

    Returns:
        str: A single string of concatenated research descriptions for the letter.
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
        page += 1
    return " ".join(collected)


async def scrape_all_descriptions(session) -> str:
    """
    Iterate through A–Z pages and scrape all research descriptions.

    Args:
        session (aiohttp.ClientSession): The active HTTP session.

    Returns:
        str: A single string of concatenated research descriptions.
    """
    texts = []
    for letter in tqdm(string.ascii_uppercase, desc="Scraping descriptions", unit="letter"):
        letter_text = await scrape_descriptions_for_letter(session, letter)
        texts.append(letter_text)
    return " ".join(texts)
