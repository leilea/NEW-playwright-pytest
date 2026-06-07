import json
import os
import glob
from datetime import datetime
import pandas as pd

from streamlit_app.utils.cache import ttl_cache

ALLURE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "allure-results")


def _load_allure_results():
    result_files = glob.glob(os.path.join(ALLURE_DIR, "*result.json"))
    rows = []
    for fp in result_files:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        feature = ""
        story = ""
        labels = data.get("labels", [])
        for label in labels:
            if label["name"] == "feature":
                feature = label["value"]
            elif label["name"] == "story":
                story = label["value"]
        rows.append({
            "name": data.get("name", ""),
            "status": data.get("status", "unknown"),
            "feature": feature,
            "story": story,
            "duration": data.get("stop", 0) - data.get("start", 0),
            "start": data.get("start", 0),
            "fullName": data.get("fullName", ""),
        })
    return pd.DataFrame(rows)


@ttl_cache(ttl_seconds=10)
def get_summary():
    df = _load_allure_results()
    if df.empty:
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "broken": 0, "pass_rate": 0}
    total = len(df)
    passed = len(df[df["status"] == "passed"])
    failed = len(df[df["status"] == "failed"])
    skipped = len(df[df["status"] == "skipped"])
    broken = len(df[df["status"] == "broken"])
    pass_rate = round(passed / total * 100, 1) if total else 0
    return {"total": total, "passed": passed, "failed": failed, "skipped": skipped, "broken": broken, "pass_rate": pass_rate}


def get_feature_stats():
    df = _load_allure_results()
    if df.empty:
        return pd.DataFrame()
    return df.groupby("feature").agg(
        total=("status", "count"),
        passed=("status", lambda x: (x == "passed").sum()),
        failed=("status", lambda x: (x == "failed").sum()),
    ).reset_index()


def get_recent_results(limit=20):
    df = _load_allure_results()
    if df.empty:
        return pd.DataFrame()
    df = df.sort_values("start", ascending=False).head(limit)
    df["time"] = df["start"].apply(lambda x: datetime.fromtimestamp(x / 1000).strftime("%H:%M:%S") if x else "")
    return df[["name", "status", "feature", "time", "duration"]]
