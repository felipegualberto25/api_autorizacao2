import json
import os
from datetime import datetime

LOG_DIR = "/app/data/logs"

def save_debug_log(job_id: str, payload: dict):
    os.makedirs(LOG_DIR, exist_ok=True)

    payload["timestamp"] = datetime.utcnow().isoformat()

    path = os.path.join(LOG_DIR, f"{job_id}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path
