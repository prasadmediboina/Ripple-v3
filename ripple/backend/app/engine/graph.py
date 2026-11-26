"""Builds the dependency graph from a snapshot ({path: source})."""
from __future__ import annotations

import builtins
from collections import defaultdict
from dataclasses import dataclass, field

from .models import CodeNode, Dependency, Unresolved
from .parser import parse_file, ParsedFile

MAX_FILE_BYTES = 1_000_000
HEURISTIC_MAX_CANDIDATES = 3


@dataclass
class DependencyGraph:
    nodes: dict[str, CodeNode] = field(default_factory=dict)
    edges: list[Dependency] = field(default_factory=list)
    unresolved: list[Unresolved] = field(default_factory=list)
    parse_errors: dict[str, str] = field(default_factory=dict)
    skipped_files: list[str] = field(default_factory=list)   # non-Python files: not analyzed

    def reverse_index(self) -> dict[str, list[Dependency]]:
        idx: dict[str, list[Dependency]] = defaultdict(list)
        for e in self.edges:
            idx[e.target_id].append(e)
        return idx


def build_graph(files: dict[str, str]) -> DependencyGraph:
    g = DependencyGraph()
    parsed: list[ParsedFile] = []
    for path, src in sorted(files.items()):
        if not path.endswith(".py"):
            g.skipped_files.append(path)
            continue
        if len(src.encode("utf-8", "ignore")) > MAX_FILE_BYTES:
            g.parse_errors[path] = "file too large; skipped"
            continue
        pf = parse_file(path, src)
        if pf.error:
            g.parse_errors[path] = pf.error
            continue
        parsed.append(pf)
        for n in pf.nodes:
            g.nodes[n.node_id] = n

    # qualified-name index: "pkg.mod.func" -> node_id
    qual_index: dict[str, str] = {}
    by_simple: dict[str, list[str]] = defaultdict(list)
    for pf in parsed:
        for n in pf.nodes:
            if n.node_type == "module":
                qual_index[pf.module] = n.node_id
                continue
            qual_index[f"{pf.module}.{n.qualname}"] = n.node_id
            by_simple[n.name].append(n.node_id)

    roots = {pf.module.split(".")[0] for pf in parsed}
    seen: set[tuple[str, str, str, int]] = set()

    def link(src: str, dst: str, rel: str, ev: str, line: int, res: str) -> None:
        if src == dst:
            return
        key = (src, dst, rel, line)
        if key in seen:
            return
        seen.add(key)
        g.edges.append(Dependency(src, dst, rel, ev, line, res))

    for pf in parsed:
        mod_pkg = pf.module
        for r in pf.refs:
            target, res = _resolve(r.expr, r.class_name, pf, qual_index, by_simple)
            if target:
                verb = "inherits from" if r.kind == "inherits" else "calls"
                link(r.owner_id, target, "inherits" if r.kind == "inherits" else "calls",
                     f"{pf.path}:{r.line} {verb} {r.expr}", r.line, res)
            else:
                head = r.expr.split(".")[0]
                if head in builtins.__dict__:
                    continue
                if head in pf.imports and pf.imports[head].split(".")[0] not in roots:
                    continue   # third-party / stdlib: outside the analyzed repository
                g.unresolved.append(Unresolved(r.owner_id, r.expr, r.line,
                                               "target could not be resolved statically (local variable, dynamic or missing)"))
        for owner, expr, line in pf.dynamic:
            g.unresolved.append(Unresolved(owner, expr, line, "dynamic call expression"))
        # module-level import edges: module -> imported symbol/module
        for alias, dotted in pf.imports.items():
            tgt = qual_index.get(dotted)
            if tgt:
                link(f"{pf.path}::<module>", tgt, "imports", f"{pf.path} imports {dotted}", 0, "exact")
    return g


def _resolve(expr: str, cls: str | None, pf: ParsedFile, qual_index: dict[str, str],
             by_simple: dict[str, list[str]]) -> tuple[str | None, str]:
    parts = expr.split(".")
    head = parts[0]
    # 1. local definition in the same module
    local = qual_index.get(f"{pf.module}.{expr}")
    if local:
        return local, "exact"
    # 2. self.method / cls.method inside a class
    if head in ("self", "cls") and cls and len(parts) == 2:
        t = qual_index.get(f"{pf.module}.{cls}.{parts[1]}")
        if t:
            return t, "exact"
    # 3. imported name (function/class) or imported module attribute
    if head in pf.imports:
        dotted = ".".join([pf.imports[head], *parts[1:]])
        t = qual_index.get(dotted)
        if t:
            return t, "exact"
    # 4. heuristic: method call on an unknown object, unique-ish simple name match
    if len(parts) >= 2 and head not in pf.imports:
        cands = by_simple.get(parts[-1], [])
        if 0 < len(cands) <= HEURISTIC_MAX_CANDIDATES:
            return cands[0] if len(cands) == 1 else cands[0], "heuristic"
    return None, "exact"
