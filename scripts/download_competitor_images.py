# scripts/download_competitor_images.py
"""
Download top images referenced in outputs/competitors/*.json
Saves into outputs/competitors/<safe_name>/images/
Persists a sha256 -> path index to outputs/competitors/images_index.json
"""
import os
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from pipeline.utils.network import safe_get
from pipeline.utils.images import is_valid_image, save_image_if_new

ROOT = Path(__file__).parent.parent
COMP_DIR = ROOT / "outputs" / "competitors"
COMP_DIR.mkdir(parents=True, exist_ok=True)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (CalycoImageBot/1.0)"})

MAX_IMAGES_PER_SITE = 5
TIMEOUT = 20

# persistent index path (sha256 -> saved_path)
IMAGES_INDEX_PATH = COMP_DIR / "images_index.json"


def sanitize_name(name: str) -> str:
    # keep safe folder names
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    name = name.replace("&", "and").strip()
    name = re.sub(r"\s+", "_", name)
    if len(name) > 80:
        name = name[:80]
    return name


def gather_json_files():
    files = []
    if (COMP_DIR / "index.json").exists():
        files.append(COMP_DIR / "index.json")
    for p in COMP_DIR.glob("*.json"):
        if p.name == "index.json":
            continue
        files.append(p)
    return files


def load_seen_map():
    if IMAGES_INDEX_PATH.exists():
        try:
            return json.load(open(IMAGES_INDEX_PATH, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def persist_seen_map(seen_map):
    try:
        IMAGES_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        json.dump(seen_map, open(IMAGES_INDEX_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("Persisted images index to:", IMAGES_INDEX_PATH)
    except Exception as e:
        print("Could not persist images index:", e)


def run():
    files = gather_json_files()
    if not files:
        print("No competitor JSON files found in", COMP_DIR)
        return

    # load persistent dedupe map (sha256 -> saved_path)
    seen_map = load_seen_map()

    total_saved = 0
    total_skipped = 0

    for p in files:
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            print("Skipping unreadable file:", p)
            continue

        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            title = entry.get("title") or entry.get("url") or "competitor"
            safe = sanitize_name(title)
            target_dir = COMP_DIR / safe / "images"
            target_dir.mkdir(parents=True, exist_ok=True)

            imgs = entry.get("images") or []
            downloaded = 0
            seen_urls = set()
            base = entry.get("url") or ""

            for img in imgs:
                if downloaded >= MAX_IMAGES_PER_SITE:
                    break
                if not img:
                    continue

                # normalize URL
                if not img.lower().startswith("http"):
                    img = urljoin(base, img)
                if img in seen_urls:
                    continue
                seen_urls.add(img)

                parsed = urlparse(img)
                fn_hint = Path(parsed.path).name or f"img_{downloaded}.jpg"

                # fetch using safe_get and SESSION
                try:
                    resp = safe_get(img, session=SESSION, timeout=TIMEOUT)
                except Exception as e:
                    # transient or blocked; skip
                    print("Failed to download", img, ":", e)
                    time.sleep(0.4)
                    continue

                content = resp.content

                # validate image bytes
                if not is_valid_image(content):
                    # skip non-image responses (SVGs, ad pixels, etc.)
                    print("Skipped invalid/non-image:", img)
                    total_skipped += 1
                    time.sleep(0.3)
                    continue

                # dedupe by content hash and persist if new
                try:
                    saved_path = save_image_if_new(content, str(target_dir), fn_hint, seen_map)
                    # If saved_path already existed in seen_map, count as already-have
                    if str(saved_path) in seen_map.values():
                        print(f"Already have image for {safe}: {Path(saved_path).name}")
                    else:
                        total_saved += 1
                        downloaded += 1
                        print(f"Saved image for {safe}: {Path(saved_path).name}")
                except Exception as e:
                    print("Error saving image", img, ":", e)

                time.sleep(0.3)

            if downloaded == 0:
                print("No new images downloaded for", safe)

    # persist seen_map for future runs
    persist_seen_map(seen_map)
    print(f"Done. Saved: {total_saved}, skipped: {total_skipped}")


if __name__ == "__main__":
    run()
