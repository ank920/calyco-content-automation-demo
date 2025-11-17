import json, os
from datetime import datetime

def write_summary(stats, errors):
    summary = {
        "timestamp": datetime.now().isoformat(),
        "stats": stats,
        "errors": errors
    }
    os.makedirs("outputs/logs", exist_ok=True)
    json.dump(summary, open("outputs/logs/run_summary.json","w"), indent=2)
