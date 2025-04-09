"""
utils.py
--------
Contains utility functions that are reused across multiple modules.
Currently includes the asynchronous page-fetching function.
"""

import asyncio
import logging
import aiohttp


async def fetch_page(session: aiohttp.ClientSession, url: str,
                     retries: int = 3, delay: float = 1) -> str:
    """
    Fetch the HTML content for a URL using asynchronous requests with retry logic.

    Args:
        session (aiohttp.ClientSession): The active HTTP session.
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
                f"Error fetching {url}: {e} (attempt {attempt + 1}/{retries})"
            )
            await asyncio.sleep(delay)
    logging.error(f"Failed to fetch {url} after {retries} attempts.")
    return ""
