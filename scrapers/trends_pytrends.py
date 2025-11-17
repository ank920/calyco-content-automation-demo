# scrapers/trends_pytrends.py
"""
Robust pytrends scraper that converts pandas objects to JSON-serializable structures.
Saves output to ../outputs/trends.json
"""
from pytrends.request import TrendReq
import json, time, os

OUT = os.path.join(os.path.dirname(__file__), "../outputs")
os.makedirs(OUT, exist_ok=True)

KEYWORDS = [
    "texture painting",
    "home painting ideas",
    "trending paint colors",
    "how to paint my kitchen",
    "contractor insights"
]

def df_to_records_safe(df):
    """
    Convert a pandas DataFrame to a JSON-serializable list of records.
    If the index is a DatetimeIndex, it will be preserved as a string in a 'date' field.
    """
    try:
        # do not import pandas at top-level to keep dependency light in some envs
        import pandas as pd
        if df is None:
            return []
        if hasattr(df, "reset_index"):
            df2 = df.reset_index()
            # attempt to infer better dtypes to avoid FutureWarning and downcasting issues
            try:
                if hasattr(df2, "infer_objects"):
                    df2 = df2.infer_objects(copy=False)
            except Exception:
                # ignore if infer_objects fails for any reason
                pass
            # convert any datetime-like index/columns to iso string
            for col in df2.columns:
                try:
                    if pd.api.types.is_datetime64_any_dtype(df2[col]):
                        df2[col] = df2[col].astype(str)
                except Exception:
                    # on any error, coerce to string safely
                    df2[col] = df2[col].astype(str)
            return df2.to_dict(orient="records")
        else:
            # fallback: try to coerce to dict
            return dict(df)
    except Exception:
        # final fallback: string representation
        return str(df)

def run_trends(save_path=os.path.join(OUT, "trends.json")):
    pytrends = TrendReq(hl='en-US', tz=330, timeout=(10,25))
    data = {"keywords": KEYWORDS, "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        pytrends.build_payload(KEYWORDS, timeframe='now 7-d')
    except Exception as e:
        data["error_build_payload"] = str(e)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Saved trends (payload error) to", save_path)
        return data

    # related queries
    try:
        related_raw = pytrends.related_queries()
        related = {}
        for k in KEYWORDS:
            try:
                top_df = related_raw.get(k, {}).get("top")
                if top_df is None:
                    related[k] = []
                else:
                    # convert DataFrame to list of dicts
                    related[k] = df_to_records_safe(top_df.head(10))
            except Exception as inner:
                related[k] = {"error": str(inner)}
        data["related"] = related
    except Exception as e:
        data["related_error"] = str(e)

    # interest over time
    try:
        iot = pytrends.interest_over_time()
        if iot is None or getattr(iot, "empty", False):
            data["interest"] = []
        else:
            # convert to list of records with date strings
            data["interest"] = df_to_records_safe(iot.tail(30))
    except Exception as e:
        data["interest_error"] = str(e)

    # Save
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Saved trends to", save_path)
    return data

if __name__ == "__main__":
    run_trends()
