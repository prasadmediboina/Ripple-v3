"""Impact traversal: multi-source reverse BFS with full path + evidence for every finding."""
from __future__ import annotations

from collections import deque

from .graph import DependencyGraph
from .models import Change, Dependency, Finding, PathStep

MAX_DEPTH = 6


def _confidence(path: list[Dependency]) -> str:
    if any(e.resolution == "heuristic" for e in path):
        return "low"
    if len(path) == 1:
        return "high"
    return "medium" if len(path) <= 3 else "low"


def find_impacts(base: DependencyGraph, head: DependencyGraph, changes: list[Change],
                 max_depth: int = MAX_DEPTH) -> list[Finding]:
    findings: dict[str, Finding] = {}
    for kind_graph, wanted in ((head, ("added", "modified")), (base, ("removed",))):
        rev = kind_graph.reverse_index()
        sources = [c.node_id for c in changes if c.kind in wanted]
        changed_ids = {c.node_id for c in changes}
        visited = set(sources)
        queue: deque[tuple[str, str, list[Dependency]]] = deque((s, s, []) for s in sources)
        while queue:
            cur, origin, path = queue.popleft()
            if len(path) >= max_depth:
                continue
            for dep in rev.get(cur, []):
                if dep.relation == "imports":
                    continue   # importing a symbol doesn't propagate impact; real use shows up as calls
                nxt = dep.source_id
                if nxt in visited:
                    continue
                visited.add(nxt)
                new_path = path + [dep]
                # Edges are stored source->target (source depends on target); we walk backwards,
                # so present the chain from the changed element outward.
                node = kind_graph.nodes.get(nxt)
                if node is None:
                    continue
                if nxt not in changed_ids:   # a changed node is already a finding of its own
                    findings.setdefault(nxt, _make_finding(kind_graph, origin, nxt, new_path))
                queue.append((nxt, origin, new_path))
    return sorted(findings.values(), key=lambda f: (f.depth, f.affected_node_id))


def _make_finding(g: DependencyGraph, origin: str, affected: str, path: list[Dependency]) -> Finding:
    node = g.nodes[affected]
    chain = list(reversed(path))   # affected -> ... -> changed
    steps = [PathStep(e.source_id, e.target_id, e.relation, e.evidence, e.resolution) for e in chain]
    first = path[0]
    reason = (f"{_short(affected)} {_verb(chain[0].relation)} {_short(chain[0].target_id)}"
              if len(chain) == 1 else
              f"{_short(affected)} reaches {_short(origin)} through {len(chain)} dependency hops")
    return Finding(
        changed_node_id=origin, affected_node_id=affected, affected_name=node.qualname,
        affected_file=node.file_path, depth=len(path), path=steps,
        confidence=_confidence(path), reason=reason, is_test=node.is_test,
    )


def _short(node_id: str) -> str:
    return node_id.split("::", 1)[-1] if "::" in node_id else node_id


def _verb(rel: str) -> str:
    return {"calls": "calls", "imports": "imports", "inherits": "inherits from"}.get(rel, rel)


def reverse_closure(g: DependencyGraph, node_id: str, max_depth: int = MAX_DEPTH) -> set[str]:
    rev = g.reverse_index()
    seen, q = {node_id}, deque([(node_id, 0)])
    while q:
        cur, d = q.popleft()
        if d >= max_depth:
            continue
        for dep in rev.get(cur, []):
            if dep.source_id not in seen:
                seen.add(dep.source_id)
                q.append((dep.source_id, d + 1))
    seen.discard(node_id)
    return seen
