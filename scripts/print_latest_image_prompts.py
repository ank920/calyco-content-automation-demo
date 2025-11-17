# scripts/print_latest_image_prompts.py
import json
from pathlib import Path
import sys

BLOG_DIR = Path("outputs/blog")
blogs = sorted(BLOG_DIR.glob("*.json"), reverse=True)
if not blogs:
    print("No blog JSON files found in outputs/blog/")
    sys.exit(1)

latest = blogs[0]
data = json.load(open(latest, encoding="utf-8"))

print("Using blog file:", latest)
print("\n--- HERO PROMPT ---")
print(data.get("image_prompt_hero") or "(no hero prompt)")
print("\n--- SUPPORT PROMPT 1 ---")
print(data.get("image_prompt_support1") or "(no support1)")
print("\n--- SUPPORT PROMPT 2 ---")
print(data.get("image_prompt_support2") or "(no support2)")
