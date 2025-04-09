"""
config.py
---------
Global configuration and constants for the UMich Faculty Research Interests Scraper.

This module sets up logging, defines constants such as file paths (located in the project root),
the base URL, and ensures that required resources (like NLTK stopwords) are available.
"""

import os
import logging
import nltk
from nltk.corpus import stopwords

# Determine the project root directory (one level above this file)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# File paths in the project root
CACHE_KEYWORDS = os.path.join(ROOT_DIR, "keywords.txt")
CACHE_DESCRIPTIONS = os.path.join(ROOT_DIR, "descriptions.txt")
COMMON_TERMS_FILE = os.path.join(ROOT_DIR, "removed_words.txt")
SCRAPER_LOG = os.path.join(ROOT_DIR, "scraper.log")

# The base URL for faculty pages.
BASE_URL = "https://midas.umich.edu/people/affiliated-faculty/"

# Output directory for images
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Configure logging to write to both the console and the root log file.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=SCRAPER_LOG,
    filemode="a"
)
# Also add a stream handler to ensure logs appear in the console.
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

# Download NLTK stopwords quietly and set up the stop words set.
nltk.download("stopwords", quiet=True)
STOP_WORDS = set(stopwords.words("english"))

# Load custom domain-specific terms to remove from text.
if os.path.exists(COMMON_TERMS_FILE):
    with open(COMMON_TERMS_FILE, "r", encoding="utf-8") as f:
        REMOVED_TERMS = [line.strip() for line in f if line.strip()]
else:
    REMOVED_TERMS = []
