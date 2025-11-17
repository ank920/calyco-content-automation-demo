#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py
Automates the full Calyco content generation pipeline.
FIXED: Preserves generated prompts from generate_prompts_via_groq_auto.py
"""
import os
import sys
import json
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] python-dotenv not installed")

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

PY = sys.executable

OUT = ROOT / "outputs"
LOGS = OUT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

SUMMARY = {
    "start": datetime.now(timezone.utc).isoformat(),
    "steps": [],
    "end": None
}

def run_cmd(cmd, step_name, allow_fail=False):
    """Run a command and log results."""
    print("\n" + "="*60)
    print(f">>> STEP: {step_name}")
    print("="*60)
    start = time.time()
    try:
        subprocess.run(cmd, check=not allow_fail)
        duration = time.time() - start
        print(f"[OK] {step_name} completed in {duration:.1f}s")
        SUMMARY["steps"].append({"name": step_name, "ok": True, "duration_s": duration})
        return True
    except subprocess.CalledProcessError as e:
        duration = time.time() - start
        print(f"[FAILED] {step_name} (code {e.returncode})")
        SUMMARY["steps"].append({
            "name": step_name, 
            "ok": False, 
            "duration_s": duration, 
            "error": str(e)
        })
        if not allow_fail:
            raise
        return False
    except Exception as e:
        duration = time.time() - start
        print(f"[ERROR] {step_name}: {e}")
        SUMMARY["steps"].append({
            "name": step_name, 
            "ok": False, 
            "duration_s": duration, 
            "error": str(e)
        })
        if not allow_fail:
            raise
        return False

def safe_rmtree_contents(path: Path):
    """Remove directory contents."""
    if not path.exists():
        return
    for child in path.iterdir():
        try:
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
        except Exception as e:
            print(f"Could not remove {child}: {e}")

def clean_outputs():
    """
    Clean outputs folder but PRESERVE prompts directory.
    This allows generate_prompts_via_groq_auto.py to run first and keep its output.
    """
    print("\n[CLEAN] Cleaning outputs folder (preserving prompts)...")
    
    # Folders to clean (NOTE: 'prompts' is NOT in this list)
    folders_to_clean = ["ads", "blog", "mdx", "seo", "social", "llm_results", "images"]
    
    for name in folders_to_clean:
        p = OUT / name
        p.mkdir(parents=True, exist_ok=True)
        safe_rmtree_contents(p)
    
    # Special handling: clear logs but keep the folder
    logs_dir = OUT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    # Don't clear logs - we'll append to run_summary.json
    
    # Special handling: clear competitors
    comp = OUT / "competitors"
    comp.mkdir(parents=True, exist_ok=True)
    safe_rmtree_contents(comp)
    
    # IMPORTANT: Ensure prompts folder exists but DON'T clear it
    prompts_dir = OUT / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Preserved prompts directory: {prompts_dir}")
    
    # Remove top-level JSONs
    for f in ["context.json", "trends.json"]:
        fp = OUT / f
        if fp.exists():
            try:
                fp.unlink()
            except Exception as e:
                print(f"Could not remove {fp}: {e}")
    
    SUMMARY["steps"].append({"name": "clean_outputs", "ok": True})
    print("[OK] Outputs cleaned (prompts preserved)")

def ensure_env_for_api():
    """Check for API key and set mode."""
    groq = os.getenv("GROQ_API_KEY")
    if groq:
        os.environ["CONTENT_MODE"] = "api"
        if not os.getenv("CONTENT_PROVIDER"):
            os.environ["CONTENT_PROVIDER"] = "GROQ"
        print("\n[API MODE] GROQ_API_KEY found -> API mode enabled")
        return True
    else:
        os.environ["CONTENT_MODE"] = "manual"
        print("\n[MANUAL MODE] GROQ_API_KEY not set")
        print("   Prompts will be written to outputs/prompts/")
        print("   To enable API mode, add GROQ_API_KEY to .env file")
        return False

def main():
    """Main pipeline execution."""
    try:
        print("\n" + "="*60)
        print(" CALYCO CONTENT PIPELINE")
        print("="*60)
        
        # 0.5. FIRST: Generate prompts via Groq (BEFORE cleaning)
        print("\n[AI PROMPTS] Generating improved prompts via Groq...")
        prompt_success = run_cmd(
            [PY, "-m", "pipeline.generate_prompts_via_groq_auto"], 
            "generate_prompts_auto", 
            allow_fail=True
        )
        
        if prompt_success:
            print("[INFO] AI-generated prompts are ready in outputs/prompts/")
        else:
            print("[WARNING] Prompt generation failed or skipped")
        
        # 0. NOW clean outputs (but preserve prompts folder)
        clean_outputs()
        
        # 1. Scrape trends
        run_cmd([PY, "-m", "scrapers.trends_pytrends"], "trends_scraper")
        
        # 2. Scrape competitors
        run_cmd([PY, "-m", "scrapers.competitor_scraper"], "competitor_scraper")
        
        # 3. Dedupe images (optional)
        if (ROOT / "scripts" / "dedupe_competitor_images.py").exists():
            run_cmd([PY, "-m", "scripts.dedupe_competitor_images"], 
                   "dedupe_images", allow_fail=True)
        
        # 4. Download competitor images
        run_cmd([PY, "-m", "scripts.download_competitor_images"], 
               "download_images")
        
        # 5. Generate placeholders (optional)
        if (ROOT / "scripts" / "generate_placeholder_images.py").exists():
            run_cmd([PY, "-m", "scripts.generate_placeholder_images"], 
                   "generate_placeholders", allow_fail=True)
        
        # 6. Write prompts (optional - skip if we already have Groq prompts)
        write_prompts = ROOT / "scripts" / "write_prompts.py"
        prompts_dir = OUT / "prompts"
        existing_prompts = list(prompts_dir.glob("*.txt")) if prompts_dir.exists() else []
        
        if write_prompts.exists() and len(existing_prompts) == 0:
            print("[INFO] No prompts found, running write_prompts as fallback...")
            run_cmd([PY, "-m", "scripts.write_prompts"], 
                   "write_prompts", allow_fail=True)
        elif len(existing_prompts) > 0:
            print(f"[INFO] Using {len(existing_prompts)} existing prompts from Groq generation")
        
        # 7. Social scraper
        run_cmd([PY, "-m", "scrapers.social_scraper"], "social_scraper")
        
        # 8. Build context.json
        run_cmd([PY, "-m", "pipeline.process_data"], "process_data")
        
        # 9. Check API availability
        api_enabled = ensure_env_for_api()
        
        # 10. Generate content
        run_cmd([PY, "-m", "pipeline.generate_content"], "generate_content")
        
        # 11. Postprocess if manual mode
        if not api_enabled:
            print("\n[MANUAL MODE] Running postprocess...")
            run_cmd([PY, "-m", "pipeline.generate_content", "postprocess"], 
                   "postprocess", allow_fail=True)
        
        # 12. Validate outputs
        run_cmd([PY, "-m", "pipeline.rules"], "validate_content")
        
        SUMMARY["end"] = datetime.now(timezone.utc).isoformat()
        SUMMARY["success"] = True
        
        print("\n" + "="*60)
        print(" PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"\nAll outputs saved to: {OUT.absolute()}")
        
    except Exception as e:
        SUMMARY["end"] = datetime.now(timezone.utc).isoformat()
        SUMMARY["success"] = False
        SUMMARY["error"] = str(e)
        print("\n" + "="*60)
        print(f" PIPELINE FAILED: {e}")
        print("="*60)
    
    # Write run summary
    try:
        with open(LOGS / "run_summary.json", "w", encoding="utf-8") as f:
            json.dump(SUMMARY, f, indent=2, ensure_ascii=False)
        print(f"\nRun summary saved to: {LOGS / 'run_summary.json'}")
    except Exception as e:
        print(f"[WARNING] Could not write run summary: {e}")
    
    if not SUMMARY.get("success"):
        print("\n[FAILED] Pipeline completed with errors")
        print(f"Check logs at: {LOGS / 'run_summary.json'}")
        sys.exit(2)
    
    print("\nPipeline finished! Check the outputs/ folder for all generated content.")

if __name__ == "__main__":
    main()
