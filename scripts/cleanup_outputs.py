# scripts/cleanup_outputs.py
import json, glob, re, pathlib
ROOT = pathlib.Path(".")
# Clean blog JSON meta fields
for f in glob.glob("outputs/blog/*.json"):
    j = json.load(open(f, encoding="utf-8"))
    # strip surrounding quotes if present
    for k in ("meta_title","meta_description"):
        if k in j and isinstance(j[k], str):
            j[k] = j[k].strip()
            # remove surrounding quotes like "\"Title\"" -> "Title"
            if j[k].startswith('"') and j[k].endswith('"'):
                j[k] = j[k][1:-1].strip()
    open(f, "w", encoding="utf-8").write(json.dumps(j, indent=2, ensure_ascii=False))
    print("Cleaned", f)

# Ensure MDX frontmatter has proper separators
for f in glob.glob("outputs/mdx/*.mdx"):
    text = open(f, encoding="utf-8").read()
    if not text.startswith("---"):
        # try to insert frontmatter separators if frontmatter lines exist
        if "title:" in text.splitlines()[0].lower():
            text = "---\n" + text
    # ensure closing separator
    if text.count("---") == 1:
        text = text.replace("\n\n", "\n\n---\n", 1)
    open(f, "w", encoding="utf-8").write(text)
    print("Checked MDX", f)
