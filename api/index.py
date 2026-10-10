import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request, Response

app = FastAPI()


# Add CORS headers to EVERY response, even when no Origin is sent
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


DATA_FILE = Path(__file__).parent / "q-vercel-latency.json"
with open(DATA_FILE) as f:
    RECORDS = json.load(f)
if isinstance(RECORDS, dict):
    RECORDS = next(v for v in RECORDS.values() if isinstance(v, list))


@app.post("/")
@app.post("/api")
async def metrics(body: dict):
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        rows = [r for r in RECORDS if r.get("region") == region]
        if not rows:
            continue
        lat = [r["latency_ms"] for r in rows]
        up = [r.get("uptime_pct", r.get("uptime")) for r in rows]
        result[region] = {
            "avg_latency": float(np.mean(lat)),
            "p95_latency": float(np.percentile(lat, 95)),
            "avg_uptime": float(np.mean(up)),
            "breaches": int(sum(1 for x in lat if x > threshold)),
        }
    return result