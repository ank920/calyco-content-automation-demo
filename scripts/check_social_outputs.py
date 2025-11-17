# scripts/check_social_outputs.py
import json, csv, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SOC_DIR = OUT / "social"
COMP_DIR = OUT / "competitors"

def check_social_folder():
    out = {}
    # 1) top-level social CSV or JSON
    social_csv = SOC_DIR / "social_posts.csv"
    out['social_posts_csv_exists'] = social_csv.exists()
    out['social_posts_sample'] = None
    if social_csv.exists():
        try:
            import pandas as pd
            df = pd.read_csv(social_csv)
            out['social_posts_columns'] = list(df.columns)
            out['social_posts_rows'] = len(df)
            out['social_posts_sample'] = df.head(3).to_dict(orient='records')
        except Exception as e:
            out['social_posts_error'] = str(e)

    # 2) competitor social JSONs (if any)
    out['competitor_social_found'] = []
    for p in COMP_DIR.glob("**/*.json"):
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
            # Heuristic: if JSON has 'posts' or 'items' or 'edge_owner_to_timeline_media' treat as social
            keys = list(j.keys()) if isinstance(j, dict) else []
            if any(k in keys for k in ('posts','items','edge_owner_to_timeline_media','data')):
                out['competitor_social_found'].append(str(p))
        except Exception:
            pass

    return out

if __name__ == "__main__":
    r = check_social_folder()
    print(json.dumps(r, indent=2))
