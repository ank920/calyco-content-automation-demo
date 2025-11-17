# scripts/regenerate_images_from_latest_blog.py
import sys
from pathlib import Path
import json

# Ensure repo root is on sys.path so `pipeline` package can be imported
REPO_ROOT = Path(__file__).resolve().parents[1]   # repo root (one level up from scripts/)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Now safe to import pipeline modules
from pipeline.image_generator import generate_image

BLOG_DIR = REPO_ROOT / "outputs" / "blog"
blogs = sorted(BLOG_DIR.glob("*.json"), reverse=True)
if not blogs:
    print("No blog JSON found in outputs/blog/")
    raise SystemExit(1)

latest = blogs[0]
print("Regenerating images for:", latest)
data = json.load(open(latest, encoding="utf-8"))

pairs = [
    ("hero", data.get("image_prompt_hero"), data.get("image_path_hero")),
    ("support1", data.get("image_prompt_support1"), data.get("image_path_support1")),
    ("support2", data.get("image_prompt_support2"), data.get("image_path_support2")),
]

for kind, prompt, existing in pairs:
    if not prompt:
        print(f"Skipping {kind}: no prompt found.")
        continue
    print(f"\n[{kind}] Prompt:\n{prompt}\n")
    size = "1024x1792" if kind == "hero" else "1024x1024"
    out_path = generate_image(prompt, size=size)
    print(f"[{kind}] Saved to: {out_path}")
    key = "image_path_hero" if kind == "hero" else ("image_path_support1" if kind=="support1" else "image_path_support2")
    data[key] = out_path

# save back the blog file with updated paths
open(latest, "w", encoding="utf-8").write(json.dumps(data, indent=2, ensure_ascii=False))
print("\nDone. Blog JSON updated with image paths.")
