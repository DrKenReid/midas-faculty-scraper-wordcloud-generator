# UMich Faculty Research Interests Scraper & Word Cloud Generator

This Python script scrapes research interests from the University of Michigan affiliated faculty pages, cleans the text by converting it to lowercase and removing common DS-related terms (loaded from an external file), NLTK stopwords, and words shorter than three characters, and then generates four word clouds. The script scrapes both the main A–Z index pages for keywords/short descriptions and individual faculty pages for full research descriptions, and it saves the word cloud images without displaying them.

## Features

* **Dual Data Sources:**\
  Scrapes the main A–Z index pages for keywords/short descriptions and follows each faculty link to scrape full research descriptions.

* **Text Cleaning:**\
  Converts all text to lowercase, removes common DS-related terms (loaded from `removed_words.txt`), filters out NLTK stopwords, and excludes words with fewer than 3 characters.

* **Word Cloud Generation:**\
  Automatically produces four word cloud images:

  * Two from the index (keywords) variant:

    * Mixed orientation (vertical & horizontal, `prefer_horizontal=0.5`)

    * Purely horizontal (`prefer_horizontal=1.0`)

  * Two from the full research descriptions (deep-scrape) variant with the same orientation settings.

* **Caching:**\
  Saves scraped data to text files (`keywords.txt` and `descriptions.txt` in the `/output/` directory) to avoid repeated scraping.

* **Output Handling:**\
  Word cloud images are saved to the `/output/` directory. The images are not displayed interactively.

## Installation

### Prerequisites

* Python 3.7 or higher

* pip

### Using a Virtual Environment (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/umich-faculty-scraper.git
   cd umich-faculty-scraper
   ```

2. **Create a virtual environment:**

   On macOS/Linux:

   ```bash
   python3 -m venv venv
   ```

   On Windows:

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   On macOS/Linux:

   ```bash
   source venv/bin/activate
   ```

   On Windows:

   ```bash
   venv\Scripts\activate
   ```

4. **Install required packages:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script by executing:

```bash
python scraper.py
```

The script will:

1. Scrape the main A–Z pages for keywords/short descriptions.

2. Follow each faculty link to scrape full research descriptions.

3. Clean the text (convert to lowercase, remove common DS terms from `removed_words.txt`, stopwords, and words shorter than 3 characters).

4. Generate and save four word clouds (two from the keywords variant and two from the descriptions variant) in the `/output/` directory.

## Configuration

The following aspects can be configured directly in the `main()` function of `scraper.py`:

* **Dark Mode:**\
  Set to `True` for a dark (black) background, or `False` for a white background.

* **Removed Words List:**\
  Common DS-related terms are loaded from the external file `removed_words.txt`. Edit this file to update the list of terms to remove.

* **Caching:**\
  The script caches scraped data in two files:

  * `keywords.txt`: Contains aggregated text from the index pages.

  * `descriptions.txt`: Contains aggregated research descriptions from individual faculty pages.

  If these files exist in the `/output/` directory, the script loads their content instead of scraping again. Delete or modify these files to force a new scrape.

## Output

* The generated word cloud images are saved to the `/output/` directory:

  * `wordcloud_keywords_mixed.png`

  * `wordcloud_keywords_horizontal.png`

  * `wordcloud_descriptions_mixed.png`

  * `wordcloud_descriptions_horizontal.png`

* After processing, a colored summary table is printed showing the number of pages scraped and the word counts for each variant.

## License

This project is licensed under the MIT License. See the [LICENSE](https://chatgpt.com/c/LICENSE) file for details.

## Acknowledgements

* [Requests](https://docs.python-requests.org/)

* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)

* [WordCloud](https://github.com/amueller/word_cloud)

* [NLTK](https://www.nltk.org/)

* [Matplotlib](https://matplotlib.org/)
