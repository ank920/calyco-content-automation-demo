import json, os, time

OUT = os.path.join(os.path.dirname(__file__), "../outputs")

def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except:
        return None

def build_context():
    trends = load(os.path.join(OUT, "trends.json"))
    competitors = load(os.path.join(OUT, "competitors", "index.json"))
    social = load(os.path.join(OUT, "social", "social_index.json"))

    ctx = {
        "trends": trends,
        "competitors": competitors,
        "social": social,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(os.path.join(OUT, "context.json"), "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, ensure_ascii=False)

    print("Saved context.json")
    return ctx

if __name__ == "__main__":
    build_context()
