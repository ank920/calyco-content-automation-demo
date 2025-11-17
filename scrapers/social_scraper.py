# scrapers/social_scraper.py
import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pipeline.utils.network import safe_get

OUTDIR = os.path.join(os.path.dirname(__file__), "../outputs/social")
os.makedirs(OUTDIR, exist_ok=True)

# use a session for keep-alive and consistent headers
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Calyco-Demo/1.0)"})

SOCIAL_URLS = [
    "https://www.instagram.com/indigopaints/",
    "https://www.linkedin.com/company/asian-paints/"
]

def fetch_meta(url):
    try:
        resp = safe_get(url, session=SESSION, timeout=20)
        text = resp.text
        soup = BeautifulSoup(text, "html.parser")

        meta = {}
        for tag in soup.find_all("meta"):
            name = tag.get("property") or tag.get("name")
            content = tag.get("content")
            if name and content:
                meta[name] = content

        return {
            "url": url,
            "status": getattr(resp, "status_code", None),
            "meta": meta,
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        # Return error object so pipeline can log and continue
        return {"url": url, "error": str(e), "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")}

def run_social():
    results = []
    for url in SOCIAL_URLS:
        print("Fetching social:", url)
        res = fetch_meta(url)
        results.append(res)
        # polite pause between requests
        time.sleep(1.0)

    out_path = os.path.join(OUTDIR, "social_index.json")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("Saved social data ->", out_path)
    except Exception as e:
        print("Failed to save social_index.json:", e)

    return results

if __name__ == "__main__":
    run_social()
