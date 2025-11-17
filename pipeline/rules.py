# pipeline/rules.py
import os
import json
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "outputs")
BLOG_DIR = os.path.join(OUT, "blog")
MDX_DIR = os.path.join(OUT, "mdx")
SOCIAL_DIR = os.path.join(OUT, "social")
SEO_DIR = os.path.join(OUT, "seo")
LLM_RESULTS_DIR = os.path.join(OUT, "llm_results")
COMPETITORS_DIR = os.path.join(OUT, "competitors")
LOGS_DIR = os.path.join(OUT, "logs")

REQUIRED_SOCIAL_COLUMNS = ["platform", "date", "time(IST)", "caption", "image_prompt", "hashtags", "utm", "post_type"]

def safe_listdir(path):
    try:
        return sorted(os.listdir(path))
    except Exception:
        return []

def check_blog_wordcount(threshold=800):
    checks = []
    files = [f for f in safe_listdir(BLOG_DIR) if f.lower().endswith(".json")]
    if not files:
        checks.append({"id": "blog_exists", "status": "fail", "message": "No blog JSON files found in outputs/blog"})
        return checks

    for f in files:
        path = os.path.join(BLOG_DIR, f)
        try:
            data = json.load(open(path, encoding="utf-8"))
            # try to compute wordcount from common fields
            wc = 0
            if "body" in data and isinstance(data["body"], str):
                wc = len(data["body"].split())
            elif "content" in data and isinstance(data["content"], list):
                # content as list of sections
                wc = sum(len(sec.get("text","").split()) for sec in data["content"])
            else:
                # try reading all string values
                all_text = " ".join([str(v) for v in data.values() if isinstance(v, str)])
                wc = len(all_text.split())

            status = "pass" if wc >= threshold else "warn"
            msg = f"{wc} words"
            if status == "warn":
                msg = f"{wc} words (< {threshold})"
            checks.append({"id": f"blog_wordcount::{f}", "status": status, "message": msg, "file": f})
        except Exception as e:
            checks.append({"id": f"blog_parse_error::{f}", "status": "fail", "message": f"Error parsing {f}: {e}"})
    return checks

def check_seo_jsonld():
    checks = []
    files = [f for f in safe_listdir(SEO_DIR) if f.lower().endswith(".jsonld") or f.lower().endswith(".json")]
    if not files:
        checks.append({"id": "seo_exists", "status": "warn", "message": "No SEO JSON-LD files found in outputs/seo"})
        return checks
    for f in files:
        path = os.path.join(SEO_DIR, f)
        try:
            data = json.load(open(path, encoding="utf-8"))
            # basic required fields
            ok = True
            missing = []
            for k in ["@context", "@type", "headline", "description"]:
                if k not in data:
                    ok = False
                    missing.append(k)
            if ok:
                checks.append({"id": f"seo_jsonld::{f}", "status": "pass", "message": "has basic fields"})
            else:
                checks.append({"id": f"seo_jsonld::{f}", "status": "warn", "message": f"missing fields: {', '.join(missing)}"})
        except Exception as e:
            checks.append({"id": f"seo_parse_error::{f}", "status": "fail", "message": f"Error parsing {f}: {e}"})
    return checks

def check_social_csv():
    checks = []
    # prefer csv file named social_posts.csv
    csv_path = os.path.join(SOCIAL_DIR, "social_posts.csv")
    if not os.path.exists(csv_path):
        # if any csv exists, check first
        csv_files = [f for f in safe_listdir(SOCIAL_DIR) if f.lower().endswith(".csv")]
        if not csv_files:
            checks.append({"id": "social_exists", "status": "warn", "message": "No social CSV found in outputs/social"})
            return checks
        csv_path = os.path.join(SOCIAL_DIR, csv_files[0])

    try:
        with open(csv_path, encoding="utf-8") as f:
            first_line = f.readline().strip()
            # If first line contains header columns
            cols = [c.strip() for c in first_line.split(",")] if first_line and "," in first_line else []
            # if header not present try to infer by counting comma count
            if cols:
                missing = [c for c in REQUIRED_SOCIAL_COLUMNS if c not in cols]
                if missing:
                    checks.append({"id": "social_columns", "status": "warn", "message": f"Missing columns: {missing}", "file": os.path.basename(csv_path)})
                else:
                    checks.append({"id": "social_columns", "status": "pass", "message": "Required columns present", "file": os.path.basename(csv_path)})
            else:
                # no header; check at least some rows exist
                rest = f.read().strip()
                if not rest:
                    checks.append({"id": "social_empty", "status": "warn", "message": f"{os.path.basename(csv_path)} appears empty"})
                else:
                    checks.append({"id": "social_no_header", "status": "warn", "message": "No header row detected; content present"})
    except Exception as e:
        checks.append({"id": "social_parse_error", "status": "fail", "message": f"Error reading social CSV: {e}"})
    return checks

def check_mdx_frontmatter():
    checks = []
    files = [f for f in safe_listdir(MDX_DIR) if f.lower().endswith(".mdx") or f.lower().endswith(".md")]
    if not files:
        checks.append({"id": "mdx_exists", "status": "warn", "message": "No MDX files found in outputs/mdx"})
        return checks
    for f in files:
        path = os.path.join(MDX_DIR, f)
        try:
            text = open(path, encoding="utf-8").read(2048)
            if text.lstrip().startswith("---"):
                checks.append({"id": f"mdx_frontmatter::{f}", "status": "pass", "message": "Frontmatter found"})
            else:
                checks.append({"id": f"mdx_frontmatter::{f}", "status": "warn", "message": "No YAML frontmatter detected"})
        except Exception as e:
            checks.append({"id": f"mdx_parse_error::{f}", "status": "fail", "message": f"Error reading {f}: {e}"})
    return checks

def check_llm_results():
    checks = []
    files = safe_listdir(LLM_RESULTS_DIR)
    if not files:
        checks.append({"id": "llm_results_exist", "status": "warn", "message": "No LLM raw responses in outputs/llm_results"})
    else:
        checks.append({"id": "llm_results_count", "status": "pass", "message": f"{len(files)} files"})
    return checks

def check_competitor_images(min_images=1):
    checks = []
    comp_dirs = [os.path.join(COMPETITORS_DIR, d) for d in safe_listdir(COMPETITORS_DIR)]
    any_image_found = False
    for d in comp_dirs:
        imgs_dir = os.path.join(d, "images")
        if os.path.isdir(imgs_dir):
            imgs = [f for f in safe_listdir(imgs_dir) if any(f.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif"])]
            if len(imgs) >= min_images:
                checks.append({"id": f"competitor_images::{os.path.basename(d)}", "status": "pass", "message": f"{len(imgs)} images"})
                any_image_found = True
            elif imgs:
                checks.append({"id": f"competitor_images::{os.path.basename(d)}", "status": "warn", "message": f"Only {len(imgs)} images found (<{min_images})"})
            else:
                checks.append({"id": f"competitor_images::{os.path.basename(d)}", "status": "warn", "message": "No images found"})
    if not comp_dirs:
        checks.append({"id": "competitors_exist", "status": "warn", "message": "No competitors directory or entries found"})
    return checks

def run_validation():
    checks = []
    # Run checks and collect
    checks.extend(check_blog_wordcount())
    checks.extend(check_seo_jsonld())
    checks.extend(check_social_csv())
    checks.extend(check_mdx_frontmatter())
    checks.extend(check_llm_results())
    checks.extend(check_competitor_images())

    summary = {
        "total": len(checks),
        "passed": sum(1 for c in checks if c.get("status") == "pass"),
        "warn": sum(1 for c in checks if c.get("status") == "warn"),
        "failed": sum(1 for c in checks if c.get("status") == "fail"),
    }

    report = {
        "run_id": datetime.utcnow().isoformat() + "Z",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
        "summary": summary
    }

    os.makedirs(LOGS_DIR, exist_ok=True)
    out_path = os.path.join(LOGS_DIR, "validation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print short summary
    print(f"Validation completed. Checks: {summary['total']}, passed: {summary['passed']}, warn: {summary['warn']}, failed: {summary['failed']}")
    print("Report written to:", out_path)

if __name__ == "__main__":
    run_validation()
