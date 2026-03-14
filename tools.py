"""Deterministic tools for building vulnerability scoring and retrofit cost estimation.

The logic here is derived from the provided "Assignment Final.xlsx" sheets:
- Score Table: maps zone / year / soft-story / structure type to points and risk tiers.
- Cost Table: provides PWD cost rates by zone and intervention method.

These functions are designed to be deterministic and usable as "tool" functions in an LLM tool-calling workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class VulnerabilityResult:
    zone: str
    zone_points: int
    year: int
    year_points: int
    soft_story: str
    soft_story_points: int
    structure_type: str
    structure_points: int
    total_score: int
    risk_tier: str


@dataclass
class RetrofitEstimate:
    intervention_type: str
    zone: str
    approximate_sqft: float
    approximate_m2: float
    num_floors: int
    unit_cost_description: str
    estimated_cost_tk: float
    details: str


# ----- Scoring rules (from Score Table sheet) -----
ZONE_POINTS = {
    "zone 1": 10,
    "zone1": 10,
    "zone 2": 25,
    "zone2": 25,
    "zone 3": 40,
    "zone3": 40,
}

YEAR_POINTS = [
    (1993, 20),  # < 1993
    (2007, 15),  # 1993-2006
    (2016, 10),  # 2007-2015
    (9999, 5),
]

SOFT_STORY_POINTS = {
    "open": 20,
    "piloti": 20,
    "open/piloti": 20,
    "open ground floor": 20,
    "piloti ground floor": 20,
    "solid": 0,
    "solid ground floor": 0,
    "no": 0,
    "none": 0,
}

STRUCTURE_TYPE_POINTS = {
    "urm": 20,
    "urm (old dhaka)": 20,
    "rc soft story": 10,
    "rc soft story (6-9 story)": 10,
    "rc infilled": 5,
    "rc infilled (engineered)": 5,
    "rc non-engineered": 8,
    "rc non-engineered (poor detailing)": 8,
    "high-rise": 5,
    "high-rise (deep pile)": 5,
}

RISK_TIERS = [
    (70, "Critical"),
    (45, "High"),
    (25, "Moderate"),
    (0, "Low"),
]


def _normalize_text(text: Optional[str]) -> str:
    if text is None:
        return ""
    return str(text).strip().lower()


def calculate_vulnerability_score(
    soil_type: str, construction_year: int, soft_story: str, structure_type: str
) -> VulnerabilityResult:
    """Calculate a deterministic vulnerability score based on the research tables.

    Args:
        soil_type: e.g. "Zone 1", "Zone 2", "Zone 3" (as per Dhaka zones).
        construction_year: The year the building was constructed.
        soft_story: A description indicating whether the ground floor is open/piloti.
        structure_type: Structural description, e.g. "RC Soft Story", "URM", etc.

    Returns:
        VulnerabilityResult containing component scores, total, and risk tier.
    """

    zone_norm = _normalize_text(soil_type)
    zone_points = ZONE_POINTS.get(zone_norm, 0)

    # Year points
    year_points = 0
    for ceiling_year, pts in YEAR_POINTS:
        if construction_year < ceiling_year:
            year_points = pts
            break

    soft_norm = _normalize_text(soft_story)
    soft_story_points = SOFT_STORY_POINTS.get(soft_norm, 0)

    struct_norm = _normalize_text(structure_type)
    structure_points = STRUCTURE_TYPE_POINTS.get(struct_norm, 0)

    total_score = zone_points + year_points + soft_story_points + structure_points

    risk_tier = "Unknown"
    for threshold, tier in RISK_TIERS:
        if total_score >= threshold:
            risk_tier = tier
            break

    return VulnerabilityResult(
        zone=soil_type,
        zone_points=zone_points,
        year=construction_year,
        year_points=year_points,
        soft_story=soft_story,
        soft_story_points=soft_story_points,
        structure_type=structure_type,
        structure_points=structure_points,
        total_score=total_score,
        risk_tier=risk_tier,
    )


# ----- Cost estimation rules (from Cost Table sheet) -----
# We keep a simplified cost database; the full table can be extended easily.
COST_RATES = {
    "zone 1": {
        "column jacketing": {
            "ground": 94232.5,
            "first": 45595,
            "escalation": 1.015,
            "unit": "m",
        },
        "shear walls": {
            "ground": 75766.25,
            "first": 23966,
            "escalation": 1.015,
            "unit": "m2",
        },
    },
    "zone 2": {
        "column jacketing": {
            "ground": 94232.5,
            "first": 45595,
            "escalation": 1.015,
            "unit": "m",
        },
        "shear walls": {
            "ground": 75766.25,
            "first": 23966,
            "escalation": 1.015,
            "unit": "m2",
        },
    },
    "zone 3": {
        "shear walls": {
            "ground": 75766.25,
            "first": 23966,
            "escalation": 1.015,
            "unit": "m2",
        },
    },
}


def estimate_retrofit_cost(
    intervention_type: str,
    approximate_sqft: float,
    zone: str = "Zone 2",
    num_floors: int = 2,
) -> RetrofitEstimate:
    """Estimate retrofit cost based on the Excel cost table.

    Args:
        intervention_type: e.g. "column jacketing" or "shear walls".
        approximate_sqft: Approximate building footprint in square feet.
        zone: The seismic/soil zone (Zone 1/2/3) used to choose rate table.
        num_floors: Number of floors for escalation cost computation.

    Returns:
        RetrofitEstimate with a rough cost estimate in Bangladeshi Taka.
    """

    zone_norm = _normalize_text(zone)
    intervention_norm = _normalize_text(intervention_type)

    zone_rates = COST_RATES.get(zone_norm)
    if not zone_rates:
        raise ValueError(
            f"Unknown zone '{zone}'. Valid choices are: {', '.join(COST_RATES.keys())}."
        )

    rate_info = zone_rates.get(intervention_norm)
    if not rate_info:
        valid = ", ".join(zone_rates.keys())
        raise ValueError(
            f"Intervention '{intervention_type}' not found for zone '{zone}'. Valid options: {valid}."
        )

    # Convert sqft to m2 for area-based rates.
    m2 = float(approximate_sqft) * 0.092903

    ground = rate_info["ground"]
    first = rate_info["first"]
    escalation = rate_info.get("escalation", 1.0)
    unit = rate_info.get("unit", "unit")

    # Base cost is ground + first floor.
    # For additional floors, apply multiplication by escalation per upper floor.
    total_cost = ground + first
    details = []
    details.append(f"Ground floor: {ground:,.2f} Tk per {unit}")
    details.append(f"First floor: {first:,.2f} Tk per {unit}")

    for additional_floor in range(2, num_floors):
        multiplier = escalation ** (additional_floor - 1)
        floor_rate = first * multiplier
        total_cost += floor_rate
        details.append(
            f"Floor {additional_floor+1} (escalation {escalation:.3f}): {floor_rate:,.2f} Tk per {unit}"
        )

    # Convert to actual cost for the building footprint.
    estimated_cost = total_cost * m2

    return RetrofitEstimate(
        intervention_type=intervention_type,
        zone=zone,
        approximate_sqft=approximate_sqft,
        approximate_m2=m2,
        num_floors=num_floors,
        unit_cost_description=f"Rates per {unit} (ground/first+escalation)",
        estimated_cost_tk=estimated_cost,
        details="; ".join(details),
    )
