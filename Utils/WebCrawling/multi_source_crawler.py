#!/usr/bin/env python3

import argparse
import os
import time   # ADDED: For adding delays
import random # ADDED: Random delay to avoid rate-limiting
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque

###################################################
# Attempt to Use cloudscraper for Cloudflare bypass
###################################################
try:
    import cloudscraper
    scraper = cloudscraper.create_scraper()  # CHANGED: Single cloudscraper session
    # If you haven't, install or upgrade via: pip install --upgrade cloudscraper
except ImportError:
    scraper = requests.Session()  # CHANGED: Fallback to requests

# For Google search; if not installed, run: pip install google
try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None
    print("WARNING: 'google' library not found. Google-based augmentation will be skipped.")

###################################################
# HEADERS: More complete, real-browser style
###################################################
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/112.0.5615.165 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",  # ADDED
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",                   # ADDED
    "Upgrade-Insecure-Requests": "1",             # ADDED
    "Cache-Control": "max-age=0"                  # ADDED
}

###################################################
# Clean text from HTML
###################################################
def clean_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove scripts and styles
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Extract text
    text = soup.get_text()

    # Clean up extra newlines/spaces
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    return text

def is_same_domain(base_url: str, target_url: str) -> bool:
    """
    Return True if target_url is in the same domain as base_url.
    """
    base_domain = urlparse(base_url).netloc
    target_domain = urlparse(target_url).netloc
    return base_domain == target_domain

###################################################
# ROBOTS.TXT CHECK
###################################################
_robots_cache = {}  # ADDED: Cache for robots.txt per domain

def is_scraping_allowed(domain: str, path: str) -> bool:
    """
    Checks the site's robots.txt to see if the path is allowed for scraping.
    If robots.txt can't be fetched or parse fails, default to True (scrape).
    """
    netloc = urlparse(domain).netloc
    robots_url = f"https://{netloc}/robots.txt"
    
    if netloc in _robots_cache:
        disallowed_paths = _robots_cache[netloc]
    else:
        disallowed_paths = []
        try:
            # Attempt to fetch robots.txt
            resp = scraper.get(robots_url, headers=HEADERS, timeout=5)
            resp.raise_for_status()
            if resp.status_code == 200:
                robots_txt = resp.text
                # parse lines beginning with 'Disallow:'
                disallowed_paths = [
                    line.split(" ")[1].strip()
                    for line in robots_txt.split("\n")
                    if line.lower().startswith("disallow:")
                ]
        except Exception as e:
            # If we can't fetch robots.txt, default to True
            print(f"[-] Couldn't fetch robots.txt at {robots_url}: {e}")

        _robots_cache[netloc] = disallowed_paths

    # If path starts with any disallowed entry, skip
    return not any(path.startswith(dp) for dp in disallowed_paths)

###################################################
# FETCH WITH RETRIES
###################################################
def fetch_url(url, retries=3, delay_range=(1, 3)):
    """
    Fetch a webpage using the single 'scraper' session, custom headers, 
    random delay, and basic retry logic.
    """
    for attempt in range(retries):
        time.sleep(random.uniform(*delay_range))  # ADDED: random short sleep
        try:
            resp = scraper.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as he:
            # If 4xx or 5xx, handle accordingly
            print(f"[-] HTTP error at {url}, attempt {attempt+1}: {he}")
            if 400 <= resp.status_code < 500:
                # Probably means a permanent block or not found => don't retry
                return None
            # Else if 5xx => keep retrying until attempts exhausted
        except requests.exceptions.RequestException as e:
            # Could be connection reset, DNS, etc.
            print(f"[-] Connection error at {url}, attempt {attempt+1}: {e}")

    # If all attempts fail
    return None

###################################################
# CRAWL WEBSITE
###################################################
def crawl_website(domain: str, max_pages: int, output_dir: str) -> None:
    visited = set()
    queue = deque([domain])
    page_count = 0

    os.makedirs(output_dir, exist_ok=True)

    while queue and page_count < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        # Check robots.txt before scraping
        if not is_scraping_allowed(domain, urlparse(url).path):
            print(f"[-] Skipping {url} due to robots.txt restrictions.")
            continue

        resp = fetch_url(url)
        if not resp:
            continue

        print(f"[DOMAIN] Crawling: {url}")
        text = clean_text(resp.text)
        page_count += 1

        filename = os.path.join(output_dir, f"domain_page_{page_count}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n\n{text}")

        # Gather same-domain links
        soup = BeautifulSoup(resp.text, "html.parser")
        for link in soup.find_all("a", href=True):
            abs_url = urljoin(url, link["href"])
            if is_same_domain(domain, abs_url) and abs_url not in visited:
                queue.append(abs_url)

###################################################
# GOOGLE AUGMENTATION
###################################################
def augment_with_google(company_name: str, google_results: int, output_dir: str) -> None:
    if not google_search:
        print("[-] googlesearch not available; skipping Google augmentation.")
        return

    os.makedirs(output_dir, exist_ok=True)

    query = f"\"{company_name}\""  # e.g. '"Syville Designs"'
    results = []
    try:
        # Retrieve up to 'google_results' URLs from Google
        for url in google_search(query, num=google_results, stop=google_results):
            results.append(url)
    except Exception as e:
        print(f"[-] Error while searching Google: {e}")
        return

    count = 0
    for url in results:
        resp = fetch_url(url)
        if not resp:
            continue

        count += 1
        print(f"[GOOGLE] Fetching: {url}")
        text = clean_text(resp.text)

        filename = os.path.join(output_dir, f"google_page_{count}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n\n{text}")

###################################################
# MAIN
###################################################
def main():
    parser = argparse.ArgumentParser(
        description="Recursively crawl a company's website + Google results, storing each page's text for RAG."
    )
    parser.add_argument("--domain", required=True, help="Company website domain (e.g. https://example.com)")
    parser.add_argument("--company_name", required=True, help="Company Name to do search on Google.")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of internal pages to crawl.")
    parser.add_argument("--google-results", type=int, default=50, help="Number of Google result pages to fetch.")
    parser.add_argument("--output-dir", default="company_data", help="Directory for storing text files.")
    
    args = parser.parse_args()

    domain_output = os.path.join(args.output_dir, "domain_pages")
    google_output = os.path.join(args.output_dir, "google_results")

    # 1. Crawl the main website
    crawl_website(args.domain, args.max_pages, domain_output)

    # 2. Augment with Google search
    augment_with_google(args.company_name, args.google_results, google_output)

    print(f"Done. Data saved under: {args.output_dir}")

if __name__ == "__main__":"
    main()