# pipeline/generate_prompts_via_groq_auto.py
"""
Auto-detect a working Groq model (free/smaller ones first), then generate production-grade prompts.
Writes outputs/prompts/{ad,blog,mdx,social}_prompt.txt and caches the selected model.

Usage:
    - Ensure GROQ_API_KEY is set in your environment (same key your pipeline already uses).
    - Run: python pipeline/generate_prompts_via_groq_auto.py

Behavior summary:
    1) If outputs/prompts/selected_model.txt exists, use that model (fast).
    2) Otherwise probe candidate models (cheap "OK" probe) and pick the first that responds.
    3) Use the selected model to expand short prompts into production prompts.
    4) If no key or no model works, write rich local fallback prompts.
"""

from pathlib import Path
import os
import json
import time
import requests
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
PROMPTS_DIR = OUTPUTS / "prompts"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

# Environment key expected
API_KEY = os.getenv("GROQ_API_KEY")

# Groq endpoint (OpenAI-compatible)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Candidate small / low-cost models to try (free-friendly first)
MODEL_PREFERENCES = [
    "mistral-7b",
    "llama-3.1-8b-instant",
    "llama-3-8b",
    "vicuna-13b",
    "mixtral-8x7b-32768",
]

# Probe message (cheap)
_PROBE_MESSAGE = "OK."

# Selected model cache file
SELECTED_MODEL_FILE = PROMPTS_DIR / "selected_model.txt"

# Default short prompts (used if no existing short prompt files exist)
DEFAULT_SHORT_PROMPTS = {
    "ad_prompt.txt": "Generate 6 short ad snippets (channel,headline,description,cta) for Google/Facebook/WhatsApp. Output CSV lines.",
    "blog_prompt.txt": "Write a 1200-1600 word SEO blog post about the primary product keyword. Return meta_title, meta_description and body in Markdown.",
    "mdx_prompt.txt": "Create an MDX product page with YAML frontmatter. Include hero, features, benefits, a comparison table, CTA, and FAQ. Output MDX only.",
    "social_prompt.txt": "Generate 3 Instagram consumer posts and 3 LinkedIn contractor posts. Output CSV lines: platform,date,time(IST),caption,image_prompt,hashtags,utm,post_type."
}

# ---------------- helpers ----------------
def human_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _load_context() -> dict:
    ctx_file = OUTPUTS / "context.json"
    if ctx_file.exists():
        try:
            return json.loads(ctx_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _write_file(fname: str, content: str) -> None:
    p = PROMPTS_DIR / fname
    p.write_text(content, encoding="utf-8")
    print(f"[PROMPTS] Wrote -> {p}")

def _local_rich_template(name: str, short_prompt: str, context: dict) -> str:
    """Return a high-quality fallback prompt (so pipeline still works offline)."""
    ts = human_ts()
    product = context.get("product", {}).get("title", "Your Product")
    primary_kw = ""
    try:
        primary_kw = context.get("trends", {}).get("keywords", [])[0]
    except Exception:
        primary_kw = ""
    base = f"""
[FALLBACK PROMPT - generated locally]
Product: {product}
Primary keyword: {primary_kw}
Generated at: {ts}

Original short prompt:
{short_prompt}

INSTRUCTIONS:
- Expand into a production-ready prompt with: purpose, input placeholders,
  expected output format (JSON schema if applicable), style & tone, length constraints,
  forbidden content, and 2 short examples (input -> expected short output).
- Keep it focused and ready to paste to an LLM.
"""
    # Short per-file specializations
    if name == "ad_prompt":
        extra = """
AD PROMPT GUIDELINES:
- Produce JSON array of ad variants with fields: channel, headline, description, cta
- Provide at least 5 variants with distinct angles: benefits, pain-solution, social-proof, urgency, ROI
- Keep headlines <= 40 chars for Meta / <= 30 for Google; description 60-90 chars.
- Provide a one-line rationale per variant.
"""
    elif name == "blog_prompt":
        extra = """
BLOG PROMPT GUIDELINES:
- Produce meta_title (<=60 chars), meta_description (<=155 chars), table of contents,
  introduction, 6+ H2 sections, actionable examples, conclusion with CTA, and FAQ (5 q).
- Target 1500-2500 words. Use primary keyword in title, intro and conclusion.
- Output as JSON: {meta_title, meta_description, body_markdown}
"""
    elif name == "mdx_prompt":
        extra = """
MDX PROMPT GUIDELINES:
- Output valid MDX only. Include YAML frontmatter with title, slug, meta fields.
- Build hero, PAS section, features bullets, comparison table, social proof, CTA, FAQ (5).
"""
    elif name == "social_prompt":
        extra = """
SOCIAL PROMPT GUIDELINES:
- Output CSV lines: platform,date,time(IST),caption,image_prompt,hashtags,utm,post_type
- Produce at least 6 posts covering Instagram, LinkedIn, Facebook, X, YouTube Shorts.
- Each caption must include: hook, insight, CTA. Provide image prompts.
"""
    else:
        extra = ""

    return (base + extra).strip()



# pipeline/generate_prompts_via_groq_auto.py
import yaml
from pathlib import Path
import re
from collections import Counter

TPL_PATH = Path("prompts/image_prompts.yaml")
if TPL_PATH.exists():
    _TPLS = yaml.safe_load(TPL_PATH.read_text())
else:
    _TPLS = {
        "hero": "Hero image for '{TITLE}'. Show an interior living room scene featuring CALYCO paint in the '{COLOR_FAMILY}' palette. Natural light, plants, warm wood tones. Photorealistic, high color accuracy. Output size: {SIZE}.",
        "product": "Close-up of painted wall with {COLOR_FAMILY} palette, showing texture and finish. Studio lighting, photorealistic. Output size: {SIZE}.",
        "social": "Social post: cozy interior corner inspired by '{TREND_KEYWORDS}', pastel tones, modern decor, space for text overlay. Photorealistic. Output size: {SIZE}."
    }

# small sanitizer / blacklist
BAN_LIST = ["sherwin-williams", "behr", "claire", "competitorbrand"]
SUFFIX_RULES = "Photorealistic, high color accuracy, no logos or text, do not mention AI."

def _extract_keywords_from_text(text, top_n=3):
    # very simple keyword extractor: split words, remove short/common words
    if not text:
        return []
    words = re.findall(r"\w+", text.lower())
    stop = {"the","and","for","with","that","this","a","an","in","on","of","to","is","are"}
    words = [w for w in words if w not in stop and len(w) > 3]
    counts = Counter(words)
    most = [w for w,_ in counts.most_common(top_n)]
    return most

def _sanitize(value: str):
    if not value:
        return ""
    v = value.strip()
    for b in BAN_LIST:
        v = v.replace(b, "")
    return v

def make_image_prompt(article: dict, image_type: str = "hero"):
    """
    article: dict, e.g. the blog_obj created in generate_content.py
    image_type: 'hero' | 'product' | 'social' | 'faq_illustration'
    returns: (prompt_text, size_str)
    """
    title = article.get("title", "") or ""
    meta = article.get("meta", {}) or {}
    body = article.get("body", "") or ""
    tags = article.get("tags") or []
    # fallback to keywords from body if tags not present
    if not tags:
        tags = _extract_keywords_from_text(body, top_n=5)

    # try to get color_family from meta or tags
    color_family = meta.get("color_family") or ""
    if not color_family:
        # look for color-like words in tags
        for t in tags:
            if any(k in t.lower() for k in ["green", "pastel", "blue", "pink", "beige", "earth", "terracotta", "sand"]):
                color_family = t
                break

    # size logic
    size = article.get("image_size_override") or ("1024x1792" if image_type == "hero" else "1024x1024")

    # prepare template and fill placeholders
    tpl = _TPLS.get(image_type) or _TPLS.get("hero")
    filled = tpl.format(
        TITLE=_sanitize(title)[:220],
        COLOR_FAMILY=_sanitize(color_family) or "neutral palette",
        TREND_KEYWORDS=", ".join(tags[:3]) if isinstance(tags, (list,tuple)) else _sanitize(tags),
        SIZE=size
    )

    # Add brand / safety suffix if not present
    if SUFFIX_RULES not in filled:
        filled = f"{filled.strip()} {SUFFIX_RULES}"

    # final sanitize: remove banned tokens (very simple)
    for bad in BAN_LIST:
        filled = filled.replace(bad, "")

    # truncate to safe length
    if len(filled) > 900:
        filled = filled[:900].rsplit(" ", 1)[0] + "."

    return filled, size



# ---------------- Groq HTTP helpers ----------------
def _post_to_groq(payload: dict, timeout: int = 25) -> Optional[requests.Response]:
    """POST to Groq endpoint, return requests.Response or None on error."""
    if not API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        return requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)
    except Exception as e:
        print("[Groq] HTTP error:", e)
        return None

def probe_model(model_name: str, retries: int = 1) -> bool:
    """Probe model availability using a tiny cheap request."""
    print(f"[Probe] Trying model '{model_name}' ...")
    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": _PROBE_MESSAGE}
        ],
        "temperature": 0.0,
        "max_tokens": 8,
    }
    for attempt in range(retries + 1):
        r = _post_to_groq(body, timeout=12)
        if r is None:
            print(f"[Probe][{model_name}] network error (attempt {attempt+1})")
            time.sleep(1 + attempt)
            continue
        if r.status_code == 200:
            try:
                data = r.json()
                content = None
                if "choices" in data and data["choices"]:
                    ch0 = data["choices"][0]
                    # OpenAI-style
                    if isinstance(ch0.get("message"), dict):
                        content = ch0["message"].get("content")
                    else:
                        content = ch0.get("text") or None
                if not content and "output_text" in data:
                    content = data["output_text"]
                if content and content.strip():
                    print(f"[Probe][{model_name}] OK -> returned content: {content.strip()[:40]!r}")
                    return True
                print(f"[Probe][{model_name}] 200 but no content; raw: {json.dumps(data)[:300]}")
                return False
            except Exception as e:
                print(f"[Probe][{model_name}] parse error: {e}; raw: {r.text[:400]}")
                return False
        else:
            print(f"[Probe][{model_name}] status {r.status_code}: {r.text.strip()[:300]}")
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1 + attempt*2)
                continue
            return False
    return False

def pick_working_model() -> Optional[str]:
    """Return cached model if present else probe preferences and return first working model."""
    # Prefer cached model to avoid probing every run
    if SELECTED_MODEL_FILE.exists():
        try:
            cached = SELECTED_MODEL_FILE.read_text(encoding="utf-8").strip()
            if cached:
                print(f"[Groq] Using cached model from {SELECTED_MODEL_FILE}: {cached}")
                return cached
        except Exception:
            pass

    if not API_KEY:
        print("[Groq] No GROQ_API_KEY in environment. Skipping model probe.")
        return None

    for model in MODEL_PREFERENCES:
        ok = probe_model(model, retries=1)
        if ok:
            print(f"[Groq] Selected model: {model}")
            try:
                SELECTED_MODEL_FILE.write_text(model, encoding="utf-8")
            except Exception:
                pass
            return model

    print("[Groq] No preferred models responded successfully.")
    return None

def call_model_for_instruction(model: str, instruction: str, max_tokens: int = 900, temperature: float = 0.2) -> Optional[str]:
    """Call selected model with a full instruction and return text output or None."""
    if not API_KEY or not model:
        return None

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an elite prompt engineer and content strategist."},
            {"role": "user", "content": instruction},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    r = _post_to_groq(body, timeout=60)
    if r is None:
        print(f"[Groq][{model}] network error during call.")
        return None
    if r.status_code == 200:
        try:
            data = r.json()
            content = None
            if "choices" in data and data["choices"]:
                ch0 = data["choices"][0]
                if isinstance(ch0.get("message"), dict):
                    content = ch0["message"].get("content")
                else:
                    content = ch0.get("text") or None
            if not content and "output_text" in data:
                content = data["output_text"]
            if not content and "output" in data and isinstance(data["output"], list) and data["output"]:
                first = data["output"][0]
                if isinstance(first, dict) and "content" in first:
                    content = first["content"]
            if content:
                return content.strip()
            print(f"[Groq][{model}] 200 OK but no content. raw: {json.dumps(data)[:800]}")
            return None
        except Exception as e:
            print(f"[Groq][{model}] parse error: {e}; raw: {r.text[:800]}")
            return None
    else:
        print(f"[Groq][{model}] status {r.status_code}: {r.text.strip()[:1000]}")
        return None

# ---------------- build detailed instruction for prompt engineering ----------------
def _build_instruction(name: str, short_prompt: str, context: dict) -> str:
    product = context.get("product", {}).get("title", "Your Product")
    trends = context.get("trends", {}).get("keywords", [])
    primary_kw = trends[0] if trends else "primary keyword"
    competitors = context.get("competitors_summary", "No competitor summary available.")
    timestamp = human_ts()

    instr = f"""
You are an expert prompt engineer and senior content strategist.
Task: Expand the SHORT prompt below into a production-ready, copy/paste prompt that downstream code can send to an LLM to generate final content.

Return ONLY the expanded prompt text. Do NOT include any extra explanation.

Requirements:
- Purpose: single-line description
- Input placeholders (e.g. {{product_name}}, {{primary_keyword}}, {{top_trends}})
- Expected output format (JSON schema or exact markdown/MDX structure)
- Style & tone rules (examples of tone)
- SEO recommendations (where applicable)
- Forbidden content rules
- 2 brief examples (input -> expected short output)
- Keep the final prompt concise (<= 3000 chars) and ready-to-use.

Context:
product_title: {product}
primary_keyword: {primary_kw}
competitor_summary: {competitors}
generated_at: {timestamp}

SHORT PROMPT ({name}):
\"\"\"{short_prompt}\"\"\"
"""
    return instr.strip()

# ---------------- main flow ----------------
def generate_prompts_auto() -> bool:
    context = _load_context()

    # Load short prompts if present; else use default short prompts
    short_prompts = {}
    for fname, default in DEFAULT_SHORT_PROMPTS.items():
        fpath = PROMPTS_DIR / fname
        try:
            if fpath.exists():
                short_prompts[fname] = fpath.read_text(encoding="utf-8")
            else:
                short_prompts[fname] = default
        except Exception:
            short_prompts[fname] = default

    # 1) pick working model (cached or probed)
    selected_model = pick_working_model()

    # 2) generate each improved prompt using selected_model or local fallback
    for fname, short in short_prompts.items():
        name = fname.replace(".txt", "")
        print(f"[PROMPTS] Generating -> {fname}")
        if selected_model:
            instruction = _build_instruction(name, short, context)
            out = call_model_for_instruction(selected_model, instruction, max_tokens=1200, temperature=0.12)
            if out:
                _write_file(fname, out)
                continue
            else:
                print(f"[PROMPTS] Model call failed for {fname} with model {selected_model}. Writing local fallback.")
                _write_file(fname, _local_rich_template(name, short, context))
        else:
            _write_file(fname, _local_rich_template(name, short, context))

    print("[PROMPTS] Completed.")
    return True

# ---------------- CLI entrypoint ----------------
if __name__ == "__main__":
    print("generate_prompts_via_groq_auto.py starting...")
    if not API_KEY:
        print("WARNING: GROQ_API_KEY not found in environment. This run will write local fallback prompts.")
    else:
        print("GROQ_API_KEY found. Attempting to auto-detect working model from preferences (cache preferred).")
    try:
        generate_prompts_auto()
    except Exception as e:
        print("Unhandled error during prompt generation:", e)
        raise
