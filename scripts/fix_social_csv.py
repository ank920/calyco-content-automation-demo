# scripts/fix_social_csv.py
"""
Ensure outputs/social/social_posts.csv has the required header.
If the CSV has rows but no header, this script will add a header
and attempt to leave the rest rows intact.
"""
import os, csv, sys

ROOT = os.getcwd()#!/usr/bin/env python3
"""
scripts/fix_social_csv.py

Normalize outputs/social/social_posts.csv:
 - ensure header exists (adds it if missing)
 - parse rows robustly (skip stray single-field caption-only lines)
 - pad/truncate rows to the REQUIRED columns
 - write atomically to avoid partial-read races

Run from repo root:
    python scripts/fix_social_csv.py
"""
import os
import csv
import sys
import tempfile
import shutil

ROOT = os.getcwd()
SOCIAL_DIR = os.path.join("outputs", "social")
SRC = os.path.join(SOCIAL_DIR, "social_posts.csv")
TMP = SRC + ".tmp"

REQUIRED = ["platform", "date", "time(IST)", "caption", "image_prompt", "hashtags", "utm", "post_type"]

def read_lines(path):
    with open(path, encoding="utf-8", newline='') as f:
        # Keep raw lines but let csv.reader handle quoting/commas
        text = f.read().splitlines()
    # Remove fully-blank lines
    return [l for l in text if l.strip()]

def detect_header_and_rows(lines):
    """
    Returns (has_header:bool, rows:list[list[str]])
    """
    if not lines:
        return False, []
    # Use csv.reader on first line to inspect field names
    first_row = next(csv.reader([lines[0]]))
    # Consider header present if any of REQUIRED appear in first row (conservative)
    header_lower = [c.strip().lower() for c in first_row]
    matched = sum(1 for r in REQUIRED if r.lower() in header_lower)
    if matched >= 2:
        # Likely has header
        # parse all lines with csv.reader
        rows = [r for r in csv.reader(lines)]
        return True, rows[1:]  # rows after header
    else:
        # No header — parse all as data rows
        rows = [r for r in csv.reader(lines)]
        return False, rows

def normalize_row(parts):
    """
    Given a list of fields, produce a row of length len(REQUIRED).
    Heuristic mapping for common cases:
      - If len == 6 and looks like (platform,date,time,caption,utm,post_type) -> insert empty image_prompt and hashtags
      - Otherwise pad with empty strings or truncate
    """
    nreq = len(REQUIRED)
    if len(parts) == nreq:
        return parts
    if len(parts) == 6:
        # assume pattern: platform,date,time,caption,utm,post_type
        return [parts[0], parts[1], parts[2], parts[3], "", "", parts[4], parts[5]]
    # general pad/truncate
    out = parts[:nreq] + [""] * max(0, nreq - len(parts))
    return out

def write_atomic(path, header, rows):
    dirpath = os.path.dirname(path)
    os.makedirs(dirpath, exist_ok=True)
    fd, tmppath = tempfile.mkstemp(prefix=".tmp_social_", dir=dirpath, text=True)
    os.close(fd)
    try:
        with open(tmppath, "w", encoding="utf-8", newline='') as f:
            w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            w.writerow(header)
            for r in rows:
                w.writerow(r)
        # atomic replace
        os.replace(tmppath, path)
    finally:
        if os.path.exists(tmppath):
            try:
                os.remove(tmppath)
            except Exception:
                pass

def main():
    if not os.path.exists(SRC):
        print("ERROR: No social_posts.csv found at", SRC)
        sys.exit(1)

    lines = read_lines(SRC)
    if not lines:
        print("ERROR: social_posts.csv is empty.")
        sys.exit(1)

    has_header, data_rows = detect_header_and_rows(lines)
    print("Detected header:", has_header)
    print("Total data rows found (after header if present):", len(data_rows))

    parsed_rows = []
    skipped = 0
    for parts in data_rows:
        # skip caption-only stray lines (single field) or completely empty rows
        if len(parts) == 0 or (len(parts) == 1 and parts[0].strip() == ""):
            skipped += 1
            continue
        if len(parts) == 1:
            # single-field — likely a stray caption or broken line: skip it
            skipped += 1
            continue
        norm = normalize_row(parts)
        parsed_rows.append(norm)

    print(f"Parsed rows: {len(parsed_rows)}  Skipped (stray/single-field): {skipped}")

    if not parsed_rows:
        print("No parsable rows after normalization. Exiting.")
        sys.exit(1)

    # Write back (atomic)
    write_atomic(SRC, REQUIRED, parsed_rows)
    print("Wrote normalized CSV with header to:", SRC)
    print("Please inspect the file and run your Streamlit app again.")

if __name__ == "__main__":
    main()

SOCIAL = os.path.join("outputs", "social", "social_posts.csv")
REQUIRED = ["platform", "date", "time(IST)", "caption", "image_prompt", "hashtags", "utm", "post_type"]

def main():
    if not os.path.exists(SOCIAL):
        print("No social_posts.csv found at", SOCIAL); sys.exit(1)

    with open(SOCIAL, encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f.readlines()]

    if not lines:
        print("social_posts.csv empty"); sys.exit(1)

    first = lines[0]
    if all(col in first for col in [","]):  # crude check for header
        cols = [c.strip() for c in first.split(",")]
        missing = [c for c in REQUIRED if c not in cols]
        if not missing:
            print("Header already present and complete.")
            sys.exit(0)
        else:
            print("Header present but missing columns:", missing)

    # Prepend a header row
    header = ",".join(REQUIRED)
    new_lines = [header] + lines
    with open(SOCIAL, "w", encoding="utf-8", newline="") as f:
        for l in new_lines:
            f.write(l + "\n")
    print("Wrote header to social_posts.csv. Please inspect the CSV and fix rows as needed.")

if __name__ == "__main__":
    main()
