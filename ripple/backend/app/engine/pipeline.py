from __future__ import annotations

from dataclasses import dataclass, field

from .diff import detect_changes
from .explain import explain_finding
from .graph import build_graph
from .impact import find_impacts
from .models import Change, Finding, TestRecommendation, to_dict
from .reviewers import suggest_reviewers
from .risk import assess_risk
from .tests_selector import select_tests

LIMITATIONS = [
    "Only Python is analyzed in this version; other languages are listed as not analyzed.",
    "Dynamic dispatch, reflection and runtime-resolved calls cannot be resolved statically.",
    "Test recommendations use static reachability, not runtime coverage data.",
    "Findings are potential impacts. A dependency does not imply a defect.",
]


@dataclass
class AnalysisReport:
    changes: list[Change]
    findings: list[Finding]
    explanations: dict[str, str]
    tests: list[TestRecommendation]
    coverage_gaps: list[str]
    unknowns: list[str]
    not_analyzed: list[str]
    risk: dict = field(default_factory=dict)
    reviewers: list = field(default_factory=list)
    limitations: list[str] = field(default_factory=lambda: list(LIMITATIONS))

    def to_dict(self) -> dict:
        return {
            "summary": {
                "changed_elements": len(self.changes),
                "potentially_affected": len(self.findings),
                "recommended_tests": len(self.tests),
                "coverage_gaps": len(self.coverage_gaps),
            },
            "changes": [to_dict(c) for c in self.changes],
            "findings": [to_dict(f) for f in self.findings],
            "explanations": self.explanations,
            "tests": [to_dict(t) for t in self.tests],
            "coverage_gaps": self.coverage_gaps,
            "unknowns": self.unknowns,
            "not_analyzed": self.not_analyzed,
            "risk": self.risk,
            "reviewers": self.reviewers,
            "limitations": self.limitations,
        }

    def to_markdown(self) -> str:
        s = self.to_dict()["summary"]
        out = ["## RIPPLE change-impact report", "",
               f"**Risk: {self.risk.get('level', 'n/a')} ({self.risk.get('score', 0)}/100)**" + (" — " + ", ".join(f["label"] for f in self.risk["factors"][:3]) if self.risk.get("factors") else ""), "",
               f"**{s['changed_elements']}** changed elements · **{s['potentially_affected']}** potentially affected · "
               f"**{s['recommended_tests']}** recommended tests · **{s['coverage_gaps']}** untested-by-reachability", ""]
        if self.changes:
            out += ["### Changed", *[f"- `{c.name}` ({c.kind}, {c.file_path})" for c in self.changes], ""]
        if self.findings:
            out += ["### Potential impacts", "| Affected | Confidence | Hops | Evidence |", "|---|---|---|---|"]
            for f in self.findings:
                out.append(f"| `{f.affected_name}` | {f.confidence} | {f.depth} | {f.path[0].evidence} |")
            out.append("")
        if self.tests:
            out += ["### Tests to run", *[f"- `{t.file_path}::{t.test_name}` — {t.reason}" for t in self.tests], ""]
        if self.coverage_gaps:
            out += ["### No test reaches these (static)", *[f"- `{g.split('::', 1)[-1]}`" for g in self.coverage_gaps], ""]
        if self.reviewers:
            out += ["### Suggested reviewers", *[f"- {r['author']} ({r['files_covered']} affected files)" for r in self.reviewers], ""]
        if self.unknowns:
            out += ["### What remains unknown", *[f"- {u}" for u in self.unknowns[:20]], ""]
        out += ["<sub>Potential impacts, not confirmed defects. " + " ".join(self.limitations[:2]) + "</sub>"]
        return "\n".join(out)


def analyze_snapshots(base_files: dict[str, str], head_files: dict[str, str], author_lookup=None) -> AnalysisReport:
    base, head = build_graph(base_files), build_graph(head_files)
    changes = detect_changes(base, head)
    findings = find_impacts(base, head, changes)
    tests, gaps = select_tests(head, changes, findings)
    changed_ids = {c.node_id for c in changes}
    unknowns = [f"{u.source_id.split('::', 1)[-1]} line {u.line}: `{u.expression}` — {u.reason}"
                for u in head.unresolved if u.source_id in changed_ids]
    unknowns += [f"{p}: {e}" for p, e in head.parse_errors.items()]
    changed_paths = {c.file_path for c in changes}
    not_analyzed = [p for p in head.skipped_files if base_files.get(p) != head_files.get(p)]
    files = sorted({c.file_path for c in changes} | {f.affected_file for f in findings if not f.is_test})
    reviewers = suggest_reviewers(author_lookup(files), files) if author_lookup and files else []
    return AnalysisReport(
        risk=assess_risk(changes, findings, tests, gaps, unknowns, not_analyzed), reviewers=reviewers,
        changes=changes, findings=findings,
        explanations={f.affected_node_id: explain_finding(f) for f in findings},
        tests=tests, coverage_gaps=gaps, unknowns=unknowns, not_analyzed=not_analyzed,
    )
