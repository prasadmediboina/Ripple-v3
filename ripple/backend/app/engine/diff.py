"""Change detection: compares two graphs node-by-node using AST hashes (formatting/comments ignored)."""
from __future__ import annotations

from .graph import DependencyGraph
from .models import Change


def detect_changes(base: DependencyGraph, head: DependencyGraph) -> list[Change]:
    changes: list[Change] = []
    for nid, n in head.nodes.items():
        old = base.nodes.get(nid)
        if old is None:
            changes.append(Change(nid, "added", n.node_type, n.file_path, n.qualname))
        elif old.body_hash != n.body_hash:
            changes.append(Change(nid, "modified", n.node_type, n.file_path, n.qualname))
    for nid, n in base.nodes.items():
        if nid not in head.nodes:
            changes.append(Change(nid, "removed", n.node_type, n.file_path, n.qualname))
    return sorted(changes, key=lambda c: (c.file_path, c.node_id))
