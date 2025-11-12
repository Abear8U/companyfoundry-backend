from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os, requests, uuid, threading, time
from dotenv import load_dotenv

load_dotenv()
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
VERCEL_PROJECT = os.getenv("VERCEL_PROJECT", "companyfoundry-affiliate")
VERCEL_ORG_ID = os.getenv("VERCEL_ORG_ID", None)

app = FastAPI(title="CompanyFoundry — Real Build")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------
# Basic hands-off presets (kept simple)
# -------------------------------------
PRESETS = [
    {"id":"affiliate_seo","label":"Affiliate + SEO Site"},
    {"id":"pod_store","label":"Print-on-Demand Store"},
    {"id":"digital_products","label":"Digital Product Store"},
    {"id":"yt_automation","label":"YouTube Automation Channel"},
    {"id":"newsletter_auto","label":"Automated Newsletter"},
]

@app.get("/presets")
def presets():
    return PRESETS

# -------------------------------------
# Simulated job runner (progress UI)
# -------------------------------------
JOBS: Dict[str, Dict[str, Any]] = {}

@app.get("/job/{job_id}")
def job(job_id: str):
    return JOBS.get(job_id, {"error":"not_found"})

# -------------------------------------
# Real deploy to Vercel
# -------------------------------------
class RealBuildRequest(BaseModel):
    preset_id: str = "affiliate_seo"
    niche: str = "rv"
    site_name: str = "my-auto-business"

AFFILIATES = {
    # KW -> link (replace with your real affiliate tags)
    "portable power station": "https://www.amazon.com/dp/B0EXAMPLE?tag=YOURTAG-20",
    "rv surge protector": "https://www.amazon.com/dp/B0EXAMPLE2?tag=YOURTAG-20",
    "travel router": "https://www.amazon.com/dp/B0EXAMPLE3?tag=YOURTAG-20",
}

def affiliate_pass(html: str) -> str:
    out = html
    for kw, link in AFFILIATES.items():
        out = out.replace(kw, f'<a href="{link}" target="_blank" rel="noopener">{kw}</a>')
    return out

def deploy_static_site(files: Dict[str, str]) -> Dict[str, Any]:
    if not VERCEL_TOKEN:
        return {"error": "Missing VERCEL_TOKEN"}
    payload = {
        "name": VERCEL_PROJECT,
        "files": [{"file": path, "data": content} for path, content in files.items()],
    }
    if VERCEL_ORG_ID:
        payload["target"] = "production"
        payload["orgId"] = VERCEL_ORG_ID

    r = requests.post(
        "https://api.vercel.com/v13/deployments",
        headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
        json=payload,
        timeout=60
    )
    if r.status_code >= 400:
        return {"error":"vercel_error","detail":r.text}
    data = r.json()
    url = f"https://{data.get('url')}" if data.get("url") else None
    return {"url": url, "deployment": data}

def make_affiliate_site(niche: str, site_name: str) -> Dict[str, str]:
    # Minimal multi-page static site (index + 3 posts)
    def page(title: str, body: str) -> str:
        body = affiliate_pass(body)
        return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#0b1220;color:#e6edf3;padding:32px;max-width:880px;margin:0 auto;}}
a{{color:#7dd3fc;text-decoration:none}} a:hover{{text-decoration:underline}}
.card{{border:1px solid #22314d;border-radius:14px;padding:22px;background:#111a2b;margin-bottom:16px}}
.btn{{display:inline-block;padding:10px 14px;border-radius:10px;background:#08f;color:#fff;text-decoration:none;font-weight:800}}
nav a{{margin-right:10px;}}
small{{opacity:.7}}
</style></head>
<body>
<nav>
  <a href="/index.html">Home</a>
  <a href="/guides/buying.html">Buying Guide</a>
  <a href="/guides/essentials.html">Essentials</a>
  <a href="/guides/connectivity.html">Connectivity</a>
</nav>
<div class="card">
  <h1>{title}</h1>
  {body}
  <p><a class="btn" href="https://buy.stripe.com/test_00EXAMPLE">Buy Something</a></p>
  <small>Built by CompanyFoundry · niche: {niche}</small>
</div>
</body></html>"""

    index = page(
        f"{niche.upper()} — Best Gear & Guides",
        f"""<p>Welcome! This site auto-builds {niche} recommendations. We update content continuously.</p>
<ul>
  <li>Portable power station tips</li>
  <li>RV surge protector checklist</li>
  <li>Budget travel router picks</li>
</ul>
<p>Start here: <a href="/guides/buying.html">Buying Guide</a></p>
"""
    )
    buying = page(
        "Buying Guide",
        """<p>When choosing gear, prioritize safety and power budget.</p>
<ul>
  <li>Consider a <b>portable power station</b> for boondocking.</li>
  <li>Always carry an <b>rv surge protector</b> to protect your rig.</li>
  <li>A compact <b>travel router</b> improves campground Wi-Fi.</li>
</ul>
"""
    )
    essentials = page(
        "Essentials",
        """<p>Essentials list for your next trip:</p>
<ol>
  <li>Leveling blocks</li>
  <li>Fresh water hose</li>
  <li>Portable power station</li>
  <li>RV surge protector</li>
</ol>
"""
    )
    connectivity = page(
        "Connectivity",
        """<p>Stay connected on the road:</p>
<ul>
  <li>Travel router</li>
  <li>Cell booster</li>
  <li>Directional antenna</li>
</ul>
"""
    )

    return {
        "index.html": index,
        "guides/buying.html": buying,
        "guides/essentials.html": essentials,
        "guides/connectivity.html": connectivity,
    }

@app.post("/build/affiliate")
def build_affiliate(req: RealBuildRequest):
    # record job
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status":"running","steps":[],"preset": req.preset_id, "niche": req.niche}

    def run():
        try:
            # 1) generate static site
            JOBS[job_id]["steps"].append({"step":"generate_site","status":"started"})
            files = make_affiliate_site(req.niche, req.site_name)
            time.sleep(0.3)
            JOBS[job_id]["steps"][-1]["status"] = "done"

            # 2) deploy to vercel
            JOBS[job_id]["steps"].append({"step":"deploy_vercel","status":"started"})
            result = deploy_static_site(files)
            time.sleep(0.3)
            JOBS[job_id]["steps"][-1]["status"] = "done"

            if "error" in result:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = result
            else:
                JOBS[job_id]["status"] = "complete"
                JOBS[job_id]["url"] = result.get("url")
        except Exception as e:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = {"msg": str(e)}

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}

@app.get("/")
def root():
    return {"message":"CompanyFoundry real builder online"}
