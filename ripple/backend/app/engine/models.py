from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

NodeType = Literal["module", "function", "method", "class"]
Resolution = Literal["exact", "heuristic"]


@dataclass(frozen=True)
class CodeNode:
    node_id: str          # "<file_path>::<qualname>"
    name: str
    qualname: str
    file_path: str
    node_type: str
    start_line: int
    end_line: int
    body_hash: str
    is_test: bool = False


@dataclass(frozen=True)
class Dependency:
    """source depends on target (source calls/imports/inherits target)."""
    source_id: str
    target_id: str
    relation: str         # calls | imports | inherits
    evidence: str         # e.g. "shop/orders.py:12 calls process_payment"
    line: int
    resolution: str = "exact"


@dataclass(frozen=True)
class Unresolved:
    """A reference RIPPLE could not resolve. Surfaced as 'what remains unknown'."""
    source_id: str
    expression: str
    line: int
    reason: str


@dataclass
class Change:
    node_id: str
    kind: str             # added | modified | removed
    node_type: str
    file_path: str
    name: str


@dataclass
class PathStep:
    source_id: str
    target_id: str
    relation: str
    evidence: str
    resolution: str


@dataclass
class Finding:
    changed_node_id: str
    affected_node_id: str
    affected_name: str
    affected_file: str
    depth: int
    path: list[PathStep]
    confidence: str       # high | medium | low
    reason: str
    is_test: bool = False
    status: str = "potential_impact"   # never "defect": a dependency is not a failure


@dataclass
class TestRecommendation:
    test_node_id: str
    test_name: str
    file_path: str
    reason: str
    covers: list[str] = field(default_factory=list)


def to_dict(obj):
    return asdict(obj)
