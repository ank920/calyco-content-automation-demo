# scrapers/competitor_scraper.py  (Windows-safe filenames)
import os
import json
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# requests session for keep-alive
import requests

# robust network helper (retry + backoff)
from pipeline.utils.network import safe_get

OUTDIR = os.path.join(os.path.dirname(__file__), "../outputs/competitors")
os.makedirs(OUTDIR, exist_ok=True)

# use a session so safe_get can reuse it
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (CalycoBot/1.0)"})

# list of competitor homepages to scrape
URLS = [
    "https://www.benjaminmoore.com/en-us",
    "https://www.behr.com",
    "https://www.asianpaints.com"
]


def slugify(s, maxlen=60):
    """Make a Windows-safe filename from string s."""
    if not s:
        s = "untitled"
    s = s.strip()
    # Remove path-invalid characters and keep alnum, dash, underscore, space
    s = re.sub(r'[<>:"/\\|?*\']+', "", s)
    s = re.sub(r'[^0-9A-Za-z\-_ ]+', "", s)
    s = s.replace(" ", "_")
    if len(s) > maxlen:
        s = s[:maxlen]
    if not s:
        s = f"file_{int(time.time())}"
    return s


def parse(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string if soup.title else base_url
    title = title.strip() if title else base_url

    paras = [p.get_text(strip=True) for p in soup.select("article p")]
    if not paras:
        paras = [p.get_text(strip=True) for p in soup.select("p")[:50]]
    snippet = " ".join(paras)[:4000]

    imgs = []
    for i in soup.select("img")[:20]:
        src = i.get("src") or i.get("data-src")
        if src:
            imgs.append(urljoin(base_url, src))

    return {
        "url": base_url,
        "title": title,
        "snippet": snippet,
        "images": imgs,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def fetch(url):
    """Fetch page HTML via safe_get (with retries). Returns None on failure."""
    try:
        resp = safe_get(url, session=SESSION, timeout=30)
        return resp.text
    except Exception as e:
        print(f"[fetch error] {url} -> {e}")
        return None


def run_competitors():
    all_data = []
    for url in URLS:
        print("Scraping:", url)
        html = fetch(url)
        if not html:
            print("Skipping (no html):", url)
            continue

        data = parse(html, url)
        all_data.append(data)

        safe_name = slugify(data.get("title", "") or url)
        fname = f"{safe_name}.json"
        outpath = os.path.join(OUTDIR, fname)

        # ensure unique filename if exists
        if os.path.exists(outpath):
            base, ext = os.path.splitext(fname)
            fname = f"{base}_{int(time.time())}{ext}"
            outpath = os.path.join(OUTDIR, fname)

        try:
            with open(outpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("Saved:", outpath)
        except Exception as e:
            print("Save error:", e)

        # be polite between site scrapes
        time.sleep(1.2)

    # write index.json
    try:
        with open(os.path.join(OUTDIR, "index.json"), "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        print("Wrote index.json")
    except Exception as e:
        print("Index save error:", e)

    return all_data


if __name__ == "__main__":
    run_competitors()
