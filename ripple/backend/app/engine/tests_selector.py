"""Test intelligence. Static reachability only: this is NOT runtime coverage and is labelled as such."""
from __future__ import annotations

from .graph import DependencyGraph
from .impact import reverse_closure
from .models import Change, Finding, TestRecommendation


def select_tests(head: DependencyGraph, changes: list[Change], findings: list[Finding]):
    recs: dict[str, TestRecommendation] = {}
    changed_ids = {c.node_id for c in changes if c.kind != "removed"}
    for c in changes:
        n = head.nodes.get(c.node_id)
        if n and n.is_test:
            recs[n.node_id] = TestRecommendation(n.node_id, n.qualname, n.file_path,
                                                 "The test itself was changed", [])
    for f in findings:
        if f.is_test:
            t = head.nodes[f.affected_node_id]
            covers = recs[t.node_id].covers if t.node_id in recs else []
            covers.append(f.changed_node_id.split("::", 1)[-1])
            recs[t.node_id] = TestRecommendation(
                t.node_id, t.qualname, t.file_path,
                f"Reaches changed code in {f.depth} dependency hop(s)", sorted(set(covers)))
    # coverage gaps: changed/affected production code that no test can statically reach
    gaps: list[str] = []
    prod = [c.node_id for c in changes if c.kind != "removed"] + [f.affected_node_id for f in findings if not f.is_test]
    for nid in dict.fromkeys(prod):
        n = head.nodes.get(nid)
        if not n or n.node_type == "module" or n.is_test:
            continue
        if not any(head.nodes[x].is_test for x in reverse_closure(head, nid) if x in head.nodes):
            gaps.append(nid)
    return sorted(recs.values(), key=lambda r: r.test_node_id), gaps
