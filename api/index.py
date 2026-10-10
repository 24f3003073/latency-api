import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA = json.loads((Path(__file__).parent / "telemetry.json").read_text())
# If the bundle is {"records": [...]}, unwrap it
if isinstance(DATA, dict):
    DATA = next(v for v in DATA.values() if isinstance(v, list))


class Query(BaseModel):
    regions: list[str]
    threshold_ms: float


def pick(rec, *names):
    for n in names:
        if n in rec:
            return rec[n]
    raise KeyError(names)


@app.post("/")
@app.post("/api")
def analyze(q: Query):
    out = {}
    for region in q.regions:
        rows = [r for r in DATA if pick(r, "region") == region]
        if not rows:
            continue
        lat = np.array([pick(r, "latency_ms", "latency") for r in rows], float)
        up = np.array([pick(r, "uptime_pct", "uptime") for r in rows], float)
        out[region] = {
            "avg_latency": float(lat.mean()),
            "p95_latency": float(np.percentile(lat, 95)),
            "avg_uptime": float(up.mean()),
            "breaches": int((lat > q.threshold_ms).sum()),
        }
    return out