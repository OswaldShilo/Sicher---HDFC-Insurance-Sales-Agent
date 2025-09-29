from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
import json
from pathlib import Path
import uuid


# JSON file paths for all insurance categories
JSON_FILES = {
    "health": Path(__file__).parent / "Health _Plans.json",
    "pension": Path(__file__).parent / "Pension_Plans.json", 
    "protection": Path(__file__).parent / "Protection_Plans.json",
    "savings": Path(__file__).parent / "Savings_Plans.json",
    "ulip": Path(__file__).parent / "ULIP_Plans.json",
    "annuity": Path(__file__).parent / "Annuity_Plans.json"
}

CATALOG_PATH = Path(__file__).parent / "catalog.json"


def load_all_policies() -> Dict[str, Any]:
    """Load all policies from category JSON files and create a unified catalog"""
    all_policies = []
    category_stats = {}
    
    for category, file_path in JSON_FILES.items():
        if file_path.exists():
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    policies = json.load(f)
                    if isinstance(policies, list):
                        # Add category and policy_id to each policy
                        for i, policy in enumerate(policies):
                            policy["category"] = category
                            policy["policy_id"] = f"{category}_{i+1}"
                            all_policies.append(policy)
                        category_stats[category] = len(policies)
                    else:
                        category_stats[category] = 0
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                category_stats[category] = 0
        else:
            category_stats[category] = 0
    
    return {
        "policies": all_policies,
        "total_policies": len(all_policies),
        "category_stats": category_stats,
        "categories": list(JSON_FILES.keys())
    }


def load_catalog() -> Dict[str, Any]:
    """Load catalog - try unified policies first, fallback to original catalog.json"""
    try:
        return load_all_policies()
    except Exception as e:
        print(f"Error loading unified policies: {e}")
        # Fallback to original catalog.json
        if CATALOG_PATH.exists():
            with CATALOG_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise FileNotFoundError("No policy data found") 


class QuoteRequest(BaseModel):
    age_band: Optional[str] = None
    dependents_count: Optional[int] = None
    annual_income_band: Optional[str] = None
    existing_cover: Optional[str] = None
    preferred_premium_band: Optional[str] = None
    risk_tolerance: Optional[str] = None
    vehicle_type: Optional[str] = None
    health_flags: Optional[List[str]] = None
    city_state: Optional[str] = None
    contact_channel: Optional[str] = None


class RecommendedPlan(BaseModel):
    policy_id: str
    name: str
    premium: int
    reason: str


class QuoteResponse(BaseModel):
    recommended: List[RecommendedPlan]
    disclaimer: str = Field(
        default=(
            "Quotes are indicative and subject to underwriting, waiting periods, and exclusions. "
            "Please review policy terms, conditions, and riders before purchase."
        )
    )


class HandoffRequest(BaseModel):
    reason: str
    customer_profile: Dict[str, Any]


class HandoffResponse(BaseModel):
    status: str
    ticket_id: str


app = FastAPI(title="Insurance Catalog & Quote Stub API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/policies")
def get_policies() -> Dict[str, Any]:
    try:
        catalog = load_catalog()
        return catalog
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


def band_to_numeric_range(band: Optional[str]) -> Optional[tuple]:
    if not band:
        return None
    band = band.strip()
    if band.startswith("<"):
        try:
            return (0, int(band[1:-1] if band.endswith("L") else band[1:]))
        except Exception:
            return None
    if band.startswith(">"):
        try:
            val = int(band[1:-1] if band.endswith("L") else band[1:])
            return (val, 10**12)
        except Exception:
            return None
    if "-" in band:
        parts = band.split("-")
        try:
            lo = int(parts[0].rstrip("Lk"))
            hi = int(parts[1].rstrip("Lk"))
            return (lo, hi)
        except Exception:
            return None
    try:
        val = int(band)
        return (val, val)
    except Exception:
        return None


def score_policy(profile: QuoteRequest, policy: Dict[str, Any]) -> float:
    score = 0.0

    # Risk tolerance mapping by type and category
    risk_map = {
        "Health Plan": {"conservative": 3, "balanced": 4, "aggressive": 3},
        "Protection Plan": {"conservative": 5, "balanced": 5, "aggressive": 5},
        "Pension Plan": {"conservative": 4, "balanced": 4, "aggressive": 3},
        "Savings Plan": {"conservative": 4, "balanced": 4, "aggressive": 3},
        "ULIP Plan": {"conservative": 2, "balanced": 4, "aggressive": 5},
        "Annuity Plan": {"conservative": 5, "balanced": 3, "aggressive": 2},
    }

    p_type = policy.get("type", "")
    p_category = policy.get("category", "")
    
    if profile.risk_tolerance and p_type in risk_map:
        score += risk_map[p_type].get(profile.risk_tolerance, 3)
    elif profile.risk_tolerance and p_category in risk_map:
        score += risk_map[p_category].get(profile.risk_tolerance, 3)

    # Dependents preference toward family health or protection
    if profile.dependents_count and profile.dependents_count > 0:
        if p_type == "Health Plan" and "Family" in policy.get("policy_name", ""):
            score += 4
        if p_type == "Protection Plan":
            score += 2

    # Vehicle type alignment for motor (not applicable to our current policies)
    if profile.vehicle_type:
        if profile.vehicle_type == "car" and p_type == "motor" and "Car" in policy.get("policy_name", ""):
            score += 4
        if profile.vehicle_type == "bike" and p_type == "motor" and ("Two-Wheeler" in policy.get("policy_name", "") or "Bike" in policy.get("policy_name", "")):
            score += 4

    # Premium band alignment
    premium_band = band_to_numeric_range(profile.preferred_premium_band)
    if premium_band:
        # choose lowest premium in table for baseline affordability
        premiums: Dict[str, int] = policy.get("premium_yearly", {})
        if premiums:
            min_premium = min(premiums.values())
            if premium_band[0] <= min_premium <= premium_band[1]:
                score += 5
            else:
                # distance penalty
                diff = min(abs(min_premium - premium_band[0]), abs(min_premium - premium_band[1]))
                score += max(0, 5 - diff / 10000.0)

    # Health flags – prefer health policies if any flags present
    if profile.health_flags and p_type == "Health Plan":
        score += 2

    # Age eligibility soft check
    if profile.age_band:
        age_range = band_to_numeric_range(profile.age_band)
        elig = policy.get("eligibility", {})
        min_age = elig.get("adult_min_age")
        max_age = elig.get("adult_max_age")
        if age_range and min_age is not None and max_age is not None:
            lo, hi = age_range
            # reward overlap
            if hi >= min_age and lo <= max_age:
                score += 2

    return score


def reason_for(policy: Dict[str, Any], profile: QuoteRequest) -> str:
    p_type = policy.get("type", "")
    name = policy.get("policy_name", "")
    premiums: Dict[str, int] = policy.get("premium_yearly", {})
    min_premium = min(premiums.values()) if premiums else 0

    if p_type == "Health Plan" and "Family" in name and (profile.dependents_count or 0) > 0:
        return "Covers dependents with balanced premium"
    if p_type == "Protection Plan":
        return "High coverage at affordable premium"
    if p_type == "Pension Plan":
        return "Secure retirement planning with guaranteed benefits"
    if p_type == "Savings Plan":
        return "Combines savings with life insurance protection"
    if p_type == "ULIP Plan":
        return "Investment-linked insurance with market exposure"
    if p_type == "Annuity Plan":
        return "Guaranteed regular income for retirement"
    return f"Lowest annual premium approx {min_premium} with broad suitability"


@app.post("/quote", response_model=QuoteResponse)
def post_quote(profile: QuoteRequest) -> QuoteResponse:
    catalog = load_catalog()
    policies: List[Dict[str, Any]] = catalog.get("policies", [])
    if not policies:
        raise HTTPException(status_code=500, detail="Catalog has no policies")

    # Score and pick top 3 policies overall (simple heuristic demo)
    scored = [
        (score_policy(profile, p), p) for p in policies
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    top3 = [p for _, p in scored[:3]]

    recommended: List[RecommendedPlan] = []
    for p in top3:
        premiums: Dict[str, int] = p.get("premium_yearly", {})
        premium_value = min(premiums.values()) if premiums else 0
        recommended.append(
            RecommendedPlan(
                policy_id=p.get("policy_id", "unknown"),
                name=p.get("policy_name", "Unknown Policy"),
                premium=premium_value,
                reason=reason_for(p, profile),
            )
        )

    return QuoteResponse(recommended=recommended)


@app.post("/handoff", response_model=HandoffResponse)
def post_handoff(payload: HandoffRequest) -> HandoffResponse:
    ticket_id = str(uuid.uuid4())[:8]
    return HandoffResponse(status="created", ticket_id=ticket_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


