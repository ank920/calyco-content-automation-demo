# scripts/verify_images.py
from pathlib import Path
import os, json, hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

def fingerprint(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            h.update(f.read(1024*64))
        return h.hexdigest()
    except:
        return None

def inspect_images():
    images = list(OUT.rglob("*.jpg")) + list(OUT.rglob("*.jpeg")) + list(OUT.rglob("*.png")) + list(OUT.rglob("*.webp"))
    report = []
    for p in images:
        size = p.stat().st_size
        fn = p.name.lower()
        fpr = fingerprint(p)
        # heuristics
        is_placeholder = "placeholder" in fn or "prompt" in fn or size < 3000
        maybe_generated = "mj" in fn or "mid" in fn or "dalle" in fn or "leonardo" in fn or "prompt" in fn
        # examine sibling txt files or prompts dir for a matching prompt
        prompt_file = p.with_suffix(".txt")
        prompt_exists = prompt_file.exists()
        report.append({
            "path": str(p.relative_to(ROOT)),
            "name": p.name,
            "size_bytes": size,
            "placeholder_guess": is_placeholder,
            "filename_hint_generated": maybe_generated,
            "prompt_file_exists": prompt_exists,
            "fingerprint": fpr
        })
    return {"count": len(report), "images": report}

if __name__ == "__main__":
    r = inspect_images()
    print(json.dumps(r, indent=2))
