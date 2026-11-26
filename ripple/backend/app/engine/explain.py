"""Explanations. Deterministic by default; an LLM can *rephrase* but never *invent* findings.

Privacy rule: no source code leaves the process unless an organization has explicitly opted in
(`llm_consent=True`) AND an LLM provider is configured. Even then only names, paths and
evidence strings are sent, never file bodies.
"""
from __future__ import annotations

from .models import Finding


def explain_finding(f: Finding) -> str:
    hops = " -> ".join(s.source_id.split("::", 1)[-1] for s in f.path) + " -> " + f.path[-1].target_id.split("::", 1)[-1]
    lines = [
        f"{f.affected_name} ({f.affected_file}) may be affected by a change to "
        f"{f.changed_node_id.split('::', 1)[-1]}.",
        f"Dependency path: {hops}.",
        f"Evidence: {f.path[0].evidence}.",
        f"Confidence: {f.confidence}. This is a potential impact, not a confirmed defect.",
    ]
    if any(s.resolution == "heuristic" for s in f.path):
        lines.append("One or more links were matched by name only; verify manually.")
    return " ".join(lines)


def llm_rephrase(text: str, llm_consent: bool, provider=None) -> str:
    if not (llm_consent and provider):
        return text
    return provider(text)   # provider is injected; see docs/SECURITY.md
