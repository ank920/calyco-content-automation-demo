#!/usr/bin/env python3
"""
Create a single canonical CSV at outputs/social/social_index.csv.

Run from repo root:
    python scripts/create_canonical_social_index.py
"""
import os
import json
import tempfile
import shutil
import time
import re
import csv
import pandas as pd

SOC_DIR = os.path.join("outputs", "social")
CSV_SRC = os.path.join(SOC_DIR, "social_posts.csv")
JSON_SRC = os.path.join(SOC_DIR, "social_index.json")
OUT = os.path.join(SOC_DIR, "social_index.csv")
TS = time.strftime("%Y%m%d%H%M%S")

# backups (created only if source exists)
BACKUP_CSV = CSV_SRC + ".bak." + TS if os.path.exists(CSV_SRC) else None
BACKUP_JSON = JSON_SRC + ".bak." + TS if os.path.exists(JSON_SRC) else None
BACKUP_OUT = OUT + ".bak." + TS if os.path.exists(OUT) else None

# canonical columns we want
COLUMNS = ["platform", "date", "time(IST)", "caption", "image_prompt", "hashtags", "utm", "post_type"]

def backup(path, dest):
    if path and os.path.exists(path):
        shutil.copy2(path, dest)
        print(f"Backed up {path} -> {dest}")

def try_pandas_read_csv(path):
    for enc in ("utf-8", "utf-8-sig", "latin1"):
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(path, encoding=enc, sep=sep, engine="python")
                print(f"pd.read_csv succeeded for {path} (enc={enc}, sep={repr(sep)})")
                return df
            except Exception:
                pass
    return None

def manual_rsplit_parser(path):
    """Robust fallback parser: rsplit each data line into COLUMNS from the right."""
    print("Manual fallback CSV parser for", path)
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        raw_lines = [ln.rstrip("\n") for ln in fh.readlines() if ln.strip()]
    if not raw_lines:
        return pd.DataFrame(columns=COLUMNS)
    # identify header if any
    header = raw_lines[0]
    expected_cols = len(COLUMNS)
    for ln in raw_lines[1:]:
        parts = ln.rsplit(",", expected_cols - 1)
        if len(parts) < expected_cols:
            parts = parts + [""] * (expected_cols - len(parts))
        left = parts[0]
        # cleanup left (caption) of triple-quote artifacts
        left = re.sub(r'"{3,}', '"', left)
        left = left.replace('""', '"')
        left = left.strip(' \t\r\n"\'')
        left = re.sub(r'^,+|,+$', '', left)
        # build canonical row with caption placed at index 3
        trailing = [p.strip() for p in parts[1:expected_cols]]
        row = [""] * expected_cols
        row[3] = left
        # map trailing values to columns 1..7 if they look like expected (best-effort)
        for i, v in enumerate(trailing, start=1):
            if i < expected_cols:
                row[i] = v
        rows.append(row)
    return pd.DataFrame(rows, columns=COLUMNS)

def read_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    try:
        parsed = json.loads(txt)
        if isinstance(parsed, list):
            return pd.json_normalize(parsed)
    except Exception:
        # try JSONL
        items = []
        for line in txt.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                pass
        if items:
            return pd.json_normalize(items)
    return None

def normalize(df):
    # ensure canonical columns exist; keep only those columns
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[COLUMNS].copy()

def dedupe(df):
    # dedupe by exact match of canonical columns
    df["_key"] = df.apply(lambda r: "|".join([str(r[c]) for c in COLUMNS]), axis=1)
    df = df.drop_duplicates(subset="_key").drop(columns=["_key"])
    return df.reset_index(drop=True)

def atomic_write(df, path):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_social_", dir=d, text=True)
    os.close(fd)
    df.to_csv(tmp, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)
    os.replace(tmp, path)
    print("Wrote canonical CSV to", path)

def main():
    # backups of sources & previous output
    if BACKUP_CSV:
        backup(CSV_SRC, BACKUP_CSV)
    if BACKUP_JSON:
        backup(JSON_SRC, BACKUP_JSON)
    if BACKUP_OUT:
        backup(OUT, BACKUP_OUT)

    parts = []
    # CSV
    if os.path.exists(CSV_SRC):
        df_csv = try_pandas_read_csv(CSV_SRC)
        if df_csv is None:
            df_csv = manual_rsplit_parser(CSV_SRC)
        parts.append(df_csv)
    # JSON
    df_json = read_json(JSON_SRC)
    if df_json is not None:
        parts.append(df_json)

    if not parts:
        print("No social CSV/JSON data found; nothing to write.")
        return

    df = pd.concat(parts, ignore_index=True, sort=False)
    df = normalize(df)
    df = dedupe(df)
    atomic_write(df, OUT)
    print("Canonical social_index.csv rows:", len(df))

if __name__ == "__main__":
    main()
