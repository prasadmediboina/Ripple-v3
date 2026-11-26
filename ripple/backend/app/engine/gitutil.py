"""Read repository snapshots straight from git objects. Never checks out or executes repository code."""
from __future__ import annotations

import subprocess


def _git(repo: str, *args: str, input: bytes | None = None) -> bytes:
    res = subprocess.run(["git", "-C", repo, *args], input=input, capture_output=True, check=True, timeout=120)
    return res.stdout


def merge_base(repo: str, a: str, b: str) -> str:
    return _git(repo, "merge-base", a, b).decode().strip()


def rev_parse(repo: str, ref: str) -> str:
    return _git(repo, "rev-parse", ref).decode().strip()


def files_at_ref(repo: str, ref: str, max_file_bytes: int = 1_000_000) -> dict[str, str]:
    """{path: source} for .py files; other files map to their blob sha so changes are still detectable."""
    listing = _git(repo, "ls-tree", "-r", "-z", "--long", ref).decode("utf-8", "replace")
    files: dict[str, str] = {}
    py: list[tuple[str, str]] = []
    for entry in filter(None, listing.split("\0")):
        meta, path = entry.split("\t", 1)
        mode, typ, sha, size = meta.split()
        if typ != "blob":
            continue
        if path.endswith(".py") and size.isdigit() and int(size) <= max_file_bytes:
            py.append((path, sha))
        else:
            files[path] = f"blob:{sha}"
    if py:
        out = _git(repo, "cat-file", "--batch", input="".join(f"{s}\n" for _, s in py).encode())
        pos = 0
        for path, _ in py:
            nl = out.index(b"\n", pos)
            size = int(out[pos:nl].split()[2])
            files[path] = out[nl + 1: nl + 1 + size].decode("utf-8", "replace")
            pos = nl + 1 + size + 1
    return files


def file_authors(repo: str, ref: str, paths: list[str], per_file: int = 50, max_files: int = 40) -> dict[str, dict[str, int]]:
    """{path: {author: commit_count}} from recent git history. Best effort; empty on failure."""
    out: dict[str, dict[str, int]] = {}
    for p in paths[:max_files]:
        try:
            names = _git(repo, "log", f"-n{per_file}", "--format=%aN", ref, "--", p).decode("utf-8", "replace").split("\n")
        except Exception:
            continue
        counts: dict[str, int] = {}
        for n in filter(None, names):
            counts[n] = counts.get(n, 0) + 1
        out[p] = counts
    return out
