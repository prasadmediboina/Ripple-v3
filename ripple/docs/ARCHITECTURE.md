# Architecture

```
GitHub PR ──webhook──▶ FastAPI ──▶ queue (inline | Celery+Redis) ──▶ run_analysis()
                         │                                              │
                     PostgreSQL ◀── findings, tests, audit, usage ◀─────┤
                                                                         ▼
             SourceProvider ─▶ {path: source} ─▶ parser ─▶ graph ─▶ diff ─▶ impact ─▶ tests ─▶ explain
```

## Engine (`backend/app/engine`)
1. **parser.py** – stdlib `ast`. Emits nodes (module/class/function/method) with an AST hash and raw references.
2. **graph.py** – resolves references to nodes: local names, `self.`/`cls.` methods, absolute and relative imports.
   Name-only matches (≤3 candidates) are kept but flagged `heuristic` (low confidence). Anything unresolved is
   recorded as an *unknown*, never silently dropped.
3. **diff.py** – compares AST hashes per node: added / modified / removed. Formatting and comments never count.
4. **impact.py** – multi-source reverse BFS (max 6 hops). Removed code is traced on the *base* graph, other changes on the *head* graph.
   Confidence: `high` = 1 exact hop, `medium` = 2–3 exact hops, `low` = longer or any heuristic edge. Import edges don't propagate impact.
5. **tests_selector.py** – tests that reach changed code, plus production code no test can statically reach.
6. **explain.py** – deterministic text. An LLM may only rephrase, and only with explicit org consent.

## Adding a language
Implement `parse_file(path, source) -> ParsedFile` for tree-sitter (same `CodeNode`/`Ref` shapes), register by file
extension in `graph.build_graph`. The graph, diff, impact and test layers are language-agnostic.

## Scaling notes
Dependency edges live in PostgreSQL tables. Introduce a graph database only when query needs justify it.
Re-index incrementally by hashing files before re-parsing (planned).
