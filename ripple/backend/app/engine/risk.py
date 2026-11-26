"""Explainable pull-request risk score. Every point is attributable to a named factor.

This is a transparent heuristic, NOT a trained bug predictor. It becomes calibrated only once
real feedback (confirmed / false-positive findings) exists to compare against.
"""
from __future__ import annotations


def assess_risk(changes, findings, tests, gaps, unknowns, not_analyzed) -> dict:
    factors: list[dict] = []

    def add(label: str, pts: int, detail: str) -> None:
        if pts > 0:
            factors.append({"label": label, "points": pts, "detail": detail})

    prod = [f for f in findings if not f.is_test]
    add("Breadth of impact", min(30, len(prod) * 2), f"{len(prod)} production elements may be affected")
    removed = sum(1 for c in changes if c.kind == "removed")
    add("Removed code", min(16, removed * 8), f"{removed} element(s) deleted; callers may break")
    add("Code no test reaches", min(24, len(gaps) * 6), f"{len(gaps)} changed or affected element(s) lack a test path")
    low = sum(1 for f in findings if f.confidence == "low")
    add("Weak evidence links", min(9, low * 3), f"{low} finding(s) rest on long paths or name-only matches")
    add("Unresolved references", min(12, len(unknowns) * 3), f"{len(unknowns)} reference(s) could not be resolved statically")
    add("Changes in unanalyzed files", min(10, len(not_analyzed) * 5), f"{len(not_analyzed)} file(s) in languages Ripple can't read yet")
    if prod and not tests:
        add("No test covers the change", 8, "Impacts were found but no existing test reaches them")

    score = min(100, sum(f["points"] for f in factors))
    level = "low" if score < 25 else "moderate" if score < 50 else "elevated" if score < 75 else "high"
    return {"score": score, "level": level, "factors": sorted(factors, key=lambda f: -f["points"]),
            "note": "Transparent heuristic, not a trained predictor. Calibrate with team feedback."}
