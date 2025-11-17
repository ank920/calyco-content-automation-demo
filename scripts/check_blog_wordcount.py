# scripts/check_blog_wordcount.py
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "outputs" / "blog"

def word_count(text):
    # naive: split on whitespace
    words = re.findall(r"\w+", text)
    return len(words)

report = []
for p in sorted(BLOG_DIR.glob("*.json")):
    j = json.loads(p.read_text(encoding='utf-8'))
    body = j.get("body", "") or j.get("content", "") or ""
    wc = word_count(body)
    status = "OK" if 1200 <= wc <= 1800 else "WARN"
    report.append({"file": str(p.name), "word_count": wc, "status": status})
print(json.dumps(report, indent=2))
