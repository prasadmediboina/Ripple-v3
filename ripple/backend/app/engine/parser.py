"""Python source parser built on the stdlib `ast` module.

Deterministic and dependency-free. Tree-sitter adapters for other languages plug in by
returning the same ParsedFile structure (see docs/ARCHITECTURE.md, "Adding a language").
"""
from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass, field

from .models import CodeNode


@dataclass
class Ref:
    owner_id: str
    kind: str            # call | inherits
    expr: str            # dotted expression, e.g. "payments.charge" or "self.helper"
    line: int
    class_name: str | None = None


@dataclass
class ParsedFile:
    path: str
    module: str
    nodes: list[CodeNode] = field(default_factory=list)
    refs: list[Ref] = field(default_factory=list)
    imports: dict[str, str] = field(default_factory=dict)   # alias -> dotted target
    dynamic: list[tuple[str, str, int]] = field(default_factory=list)  # (owner, expr, line)
    error: str | None = None


def module_name(path: str) -> str:
    p = path[:-3] if path.endswith(".py") else path
    parts = [x for x in p.split("/") if x]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_test_path(path: str) -> bool:
    base = path.rsplit("/", 1)[-1]
    return (
        base.startswith("test_")
        or base.endswith("_test.py")
        or "/tests/" in f"/{path}"
        or "/test/" in f"/{path}"
    )


def _hash(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def _resolve_relative(module: str, is_pkg: bool, level: int, name: str | None) -> str:
    parts = module.split(".") if module else []
    pkg = parts if is_pkg else parts[:-1]
    if level > 1:
        pkg = pkg[: len(pkg) - (level - 1)]
    base = ".".join(pkg)
    return ".".join(x for x in (base, name) if x)


def parse_file(path: str, source: str) -> ParsedFile:
    mod = module_name(path)
    pf = ParsedFile(path=path, module=mod)
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        pf.error = f"syntax error line {exc.lineno}: {exc.msg}"
        return pf

    test_file = is_test_path(path)
    is_pkg = path.endswith("__init__.py")
    module_id = f"{path}::<module>"

    def collect_refs(root: ast.AST, owner: str, cls: str | None) -> None:
        for n in ast.walk(root):
            if isinstance(n, ast.Call):
                expr = _dotted(n.func)
                if expr:
                    pf.refs.append(Ref(owner, "call", expr, n.lineno, cls))
                else:
                    pf.dynamic.append((owner, ast.unparse(n.func)[:80], n.lineno))

    def collect_imports(root: ast.AST) -> None:
        for n in ast.walk(root):
            if isinstance(n, ast.Import):
                for a in n.names:
                    pf.imports[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
            elif isinstance(n, ast.ImportFrom):
                base = _resolve_relative(mod, is_pkg, n.level, n.module) if n.level else (n.module or "")
                for a in n.names:
                    if a.name != "*":
                        pf.imports[a.asname or a.name] = f"{base}.{a.name}" if base else a.name

    collect_imports(tree)

    def add(name: str, qual: str, ntype: str, node: ast.AST, h: str) -> str:
        nid = f"{path}::{qual}"
        pf.nodes.append(CodeNode(
            node_id=nid, name=name, qualname=qual, file_path=path, node_type=ntype,
            start_line=getattr(node, "lineno", 1), end_line=getattr(node, "end_lineno", 1),
            body_hash=h,
            is_test=test_file and ntype in ("function", "method") and name.startswith("test"),
        ))
        return nid

    def visit_body(body: list[ast.stmt], scope: list[str], owner: str, cls: str | None) -> list[ast.stmt]:
        """Returns the 'loose' statements (non def/class) of this scope."""
        loose: list[ast.stmt] = []
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = ".".join(scope + [stmt.name])
                nid = add(stmt.name, qual, "method" if cls else "function", stmt,
                          _hash(ast.dump(stmt, include_attributes=False)))
                collect_refs(stmt, nid, cls)
            elif isinstance(stmt, ast.ClassDef):
                qual = ".".join(scope + [stmt.name])
                cid = f"{path}::{qual}"
                inner_loose = [s for s in stmt.body if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
                header = [ast.dump(x, include_attributes=False) for x in (*stmt.bases, *stmt.keywords, *stmt.decorator_list)]
                body_dump = [ast.dump(s, include_attributes=False) for s in inner_loose]
                add(stmt.name, qual, "class", stmt, _hash(*header, *body_dump))
                for b in stmt.bases:
                    e = _dotted(b)
                    if e:
                        pf.refs.append(Ref(cid, "inherits", e, stmt.lineno, None))
                for s in inner_loose:
                    collect_refs(s, cid, stmt.name)
                visit_body(stmt.body, scope + [stmt.name], cid, stmt.name)
            else:
                loose.append(stmt)
        return loose

    loose = visit_body(tree.body, [], module_id, None)
    add("<module>", "<module>", "module", tree,
        _hash(*[ast.dump(s, include_attributes=False) for s in loose]))
    for s in loose:
        collect_refs(s, module_id, None)
    return pf
