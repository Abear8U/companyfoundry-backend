from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List

app = FastAPI(title="CompanyFoundry – Real Builder")

# ----- CORS -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can replace * with your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Root Route -----
@app.get("/")
def root():
    return {"message": "CompanyFoundry real builder online"}

# ----- Health Check -----
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# ----- Data Models -----
class PlanIn(BaseModel):
    amount: float
    state: str
    industry: str

class PlanOut(BaseModel):
    entity: str
    est_costs: dict
    next_steps: List[str]

# ----- Plan Endpoint -----
@app.post("/plan", response_model=PlanOut)
def make_plan(inp: PlanIn):
    base = 650   # formation + EIN + BOI
    lic = 200    # placeholder for local licensing
    web = 300    # domain + hosting
    total = base + lic + web

    return PlanOut(
        entity="LLC",
        est_costs={
            "formation": base,
            "licenses": lic,
            "web": web,
            "reserve": max(inp.amount - total, 0)
        },
        next_steps=[
            f"File {inp.state} LLC & get EIN",
            "Run license search (NAICS + ZIP)",
            "Buy domain & deploy site",
        ],
    )
