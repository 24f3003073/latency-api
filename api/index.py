from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

app = FastAPI()


# CORS: add the headers to EVERY response, even if the request has no Origin
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

DATA = [{"region":"apac","service":"catalog","latency_ms":223.61,"uptime_pct":98.977,"timestamp":20250301},{"region":"apac","service":"catalog","latency_ms":166.52,"uptime_pct":97.575,"timestamp":20250302},{"region":"apac","service":"catalog","latency_ms":174.6,"uptime_pct":98.595,"timestamp":20250303},{"region":"apac","service":"checkout","latency_ms":194.78,"uptime_pct":98.917,"timestamp":20250304},{"region":"apac","service":"catalog","latency_ms":161.8,"uptime_pct":99.181,"timestamp":20250305},{"region":"apac","service":"analytics","latency_ms":145.3,"uptime_pct":98.037,"timestamp":20250306},{"region":"apac","service":"checkout","latency_ms":144.75,"uptime_pct":98.773,"timestamp":20250307},{"region":"apac","service":"recommendations","latency_ms":219.48,"uptime_pct":98.849,"timestamp":20250308},{"region":"apac","service":"recommendations","latency_ms":214.39,"uptime_pct":97.828,"timestamp":20250309},{"region":"apac","service":"support","latency_ms":168.23,"uptime_pct":99.391,"timestamp":20250310},{"region":"apac","service":"analytics","latency_ms":211.11,"uptime_pct":97.908,"timestamp":20250311},{"region":"apac","service":"payments","latency_ms":146.05,"uptime_pct":98.792,"timestamp":20250312},{"region":"emea","service":"catalog","latency_ms":197.5,"uptime_pct":98.47,"timestamp":20250301},{"region":"emea","service":"catalog","latency_ms":185.51,"uptime_pct":98.191,"timestamp":20250302},{"region":"emea","service":"checkout","latency_ms":189.16,"uptime_pct":97.954,"timestamp":20250303},{"region":"emea","service":"recommendations","latency_ms":148.71,"uptime_pct":99.24,"timestamp":20250304},{"region":"emea","service":"catalog","latency_ms":132.42,"uptime_pct":98.392,"timestamp":20250305},{"region":"emea","service":"catalog","latency_ms":140.3,"uptime_pct":97.148,"timestamp":20250306},{"region":"emea","service":"recommendations","latency_ms":203.46,"uptime_pct":99.213,"timestamp":20250307},{"region":"emea","service":"payments","latency_ms":210.03,"uptime_pct":98.391,"timestamp":20250308},{"region":"emea","service":"recommendations","latency_ms":167.5,"uptime_pct":97.935,"timestamp":20250309},{"region":"emea","service":"checkout","latency_ms":169.49,"uptime_pct":97.271,"timestamp":20250310},{"region":"emea","service":"checkout","latency_ms":169.24,"uptime_pct":97.523,"timestamp":20250311},{"region":"emea","service":"catalog","latency_ms":173.62,"uptime_pct":97.235,"timestamp":20250312},{"region":"amer","service":"payments","latency_ms":144.23,"uptime_pct":97.233,"timestamp":20250301},{"region":"amer","service":"recommendations","latency_ms":139.25,"uptime_pct":99.088,"timestamp":20250302},{"region":"amer","service":"analytics","latency_ms":205.91,"uptime_pct":98.696,"timestamp":20250303},{"region":"amer","service":"support","latency_ms":120.19,"uptime_pct":98.298,"timestamp":20250304},{"region":"amer","service":"support","latency_ms":181.14,"uptime_pct":97.144,"timestamp":20250305},{"region":"amer","service":"recommendations","latency_ms":178.64,"uptime_pct":98.251,"timestamp":20250306},{"region":"amer","service":"recommendations","latency_ms":193.98,"uptime_pct":97.933,"timestamp":20250307},{"region":"amer","service":"analytics","latency_ms":153.51,"uptime_pct":97.846,"timestamp":20250308},{"region":"amer","service":"checkout","latency_ms":150.71,"uptime_pct":98.967,"timestamp":20250309},{"region":"amer","service":"catalog","latency_ms":155.94,"uptime_pct":97.508,"timestamp":20250310},{"region":"amer","service":"analytics","latency_ms":146.41,"uptime_pct":97.171,"timestamp":20250311},{"region":"amer","service":"support","latency_ms":134.14,"uptime_pct":99.141,"timestamp":20250312}]


def percentile(values, p):
    v = sorted(values)
    k = (len(v) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


class Query(BaseModel):
    regions: list[str]
    threshold_ms: float


def compute(q: Query):
    out = {}
    for region in q.regions:
        rows = [d for d in DATA if d["region"] == region]
        if not rows:
            continue
        lat = [d["latency_ms"] for d in rows]
        up = [d["uptime_pct"] for d in rows]
        out[region] = {
            "avg_latency": sum(lat) / len(lat),
            "p95_latency": percentile(lat, 95),
            "avg_uptime": sum(up) / len(up),
            "breaches": sum(1 for x in lat if x > q.threshold_ms),
        }
    return out


@app.post("/")
@app.post("/api")
def metrics(q: Query):
    result = compute(q)
    return {**result, "regions": result}
