# scripts/write_prompts.py
import os
import json

ROOT = os.path.dirname(__file__)
OUT = os.path.join(ROOT, "..", "outputs")
PROMPTS_DIR = os.path.join(OUT, "prompts")
os.makedirs(PROMPTS_DIR, exist_ok=True)

# Load context if available
context_path = os.path.join(OUT, "context.json")
context = {}
if os.path.exists(context_path):
    try:
        with open(context_path, encoding="utf-8") as fh:
            context = json.load(fh)
    except Exception:
        context = {}

def build_blog_prompt(ctx):
    trends = ctx.get("trends", {}).get("related", {})
    # safe stringify of trends (limit length)
    trends_json = json.dumps(trends, indent=2, ensure_ascii=False)
    trends_snippet = trends_json[:3500]

    comps = ctx.get("competitors", [])[:2]
    comp_text_lines = []
    for c in comps:
        title = c.get("title", "") or c.get("url", "")
        snippet = c.get("snippet", "") or ""
        comp_text_lines.append(f"{title}: {snippet[:400]}")
    comp_text = "\n\n".join(comp_text_lines)

    parts = [
        "Write a 1200-1600 word SEO blog post for Calyco (online-first paint brand).",
        "Context (top trends and competitor inspiration):",
        trends_snippet,
        "",
        "Competitor snippets:",
        comp_text,
        "",
        "Requirements:",
        "- Title, meta_title (<=60 chars), meta_description (<=155 chars)",
        "- 4+ subheads, bullets, FAQs (3)",
        "- 3 image prompts",
        "- Tone: helpful, modern, performance-first (mention low-VOC, washable, fast recoat)",
        "- Do NOT mention AI or imply the content was AI-generated.",
        "Return the article text clearly and label meta lines if possible."
    ]
    return "\n\n".join(parts)

def build_mdx_prompt(ctx):
    return (
        "Create an MDX product page for 'Calyco Super Emulsion - Interior'.\n\n"
        "Include YAML frontmatter with title, slug, meta.title, meta.description, a short description, "
        "3 feature bullets (mention low-VOC, washable, fast recoat), technical specs and a CTA. Output MDX only."
    )

def build_social_prompt(ctx):
    trends_keys = list(ctx.get("trends", {}).get("related", {}).keys())[:8]
    return (
        f"Using these trending terms: {trends_keys}\n\n"
        "Generate 3 Instagram consumer posts and 3 LinkedIn contractor posts.\n"
        "Output as CSV lines: platform,date,time,caption,image_prompt,hashtags,utm,post_type\n"
        "Keep concise, brand-aligned, and never mention AI."
    )

# static ad prompt
ad_prompt_text = (
    "Generate 6 short ad snippets (channel,headline,description,cta) for Google/Facebook/WhatsApp. "
    "Keep them punchy and performance-focused for Calyco. Output CSV lines."
)

prompts = {
    "blog_prompt.txt": build_blog_prompt(context),
    "mdx_prompt.txt": build_mdx_prompt(context),
    "social_prompt.txt": build_social_prompt(context),
    "ad_prompt.txt": ad_prompt_text
}

for filename, text in prompts.items():
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Wrote:", path)
