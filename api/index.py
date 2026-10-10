import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}


@app.middleware("http")
async def cors(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(status_code=200, headers=CORS_HEADERS)
    try:
        response = await call_next(request)
    except Exception as e:
        response = JSONResponse({"error": str(e)}, status_code=500)
    for k, v in CORS_HEADERS.items():
        response.headers[k] = v  # sets (replaces), never duplicates
    return response


DATA_FILE = Path(__file__).parent / "q-vercel-latency.json"
with open(DATA_FILE) as f:
    RECORDS = json.load(f)
if isinstance(RECORDS, dict):
    RECORDS = next(v for v in RECORDS.values() if isinstance(v, list))


@app.get("/")
@app.get("/api")
async def health():
    return {"status": "ok"}


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