# scripts/dedupe_competitor_images.py
"""
One-off dedupe: compute sha256 for all images under outputs/competitors/*/images/,
keep the first occurrence, move duplicates to outputs/competitors/duplicates/,
and write outputs/competitors/images_index.json mapping sha256 -> kept_path.
"""
import os
import hashlib
import json
from pathlib import Path
from shutil import move

ROOT = Path(__file__).parent.parent
COMP_DIR = ROOT / "outputs" / "competitors"
DUP_DIR = COMP_DIR / "duplicates"
IMAGES_INDEX_PATH = COMP_DIR / "images_index.json"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def gather_images():
    imgs = []
    if not COMP_DIR.exists():
        return imgs
    for sub in COMP_DIR.iterdir():
        if not sub.is_dir():
            continue
        images_dir = sub / "images"
        if images_dir.is_dir():
            for f in images_dir.iterdir():
                if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                    imgs.append(f)
    return imgs

def run():
    imgs = gather_images()
    if not imgs:
        print("No images found under", COMP_DIR)
        return

    seen = {}
    duplicates_moved = 0
    kept = 0
    DUP_DIR.mkdir(parents=True, exist_ok=True)

    for p in sorted(imgs):
        try:
            digest = sha256_file(p)
        except Exception as e:
            print("Could not hash", p, ":", e)
            continue

        if digest in seen:
            # duplicate -> move to duplicates folder preserving structure
            rel = p.relative_to(COMP_DIR)
            target = DUP_DIR / rel.parent.name
            target.mkdir(parents=True, exist_ok=True)
            dest = target / p.name
            try:
                move(str(p), str(dest))
                duplicates_moved += 1
                print("Moved duplicate:", p, "->", dest)
            except Exception as e:
                print("Failed to move duplicate", p, ":", e)
        else:
            # first-seen: keep and record absolute path
            seen[digest] = str(p.resolve())
            kept += 1

    # write index mapping
    try:
        with open(IMAGES_INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(seen, f, indent=2, ensure_ascii=False)
        print("Wrote images index:", IMAGES_INDEX_PATH)
    except Exception as e:
        print("Failed to write images index:", e)

    print(f"Done. Kept: {kept}, duplicates moved: {duplicates_moved}")

if __name__ == "__main__":
    run()
