from __future__ import annotations

from collections import Counter, defaultdict


def suggest_reviewers(file_authors: dict[str, dict[str, int]], files: list[str], limit: int = 3) -> list[dict]:
    """Rank people by how many of the affected files they have recently changed."""
    totals: Counter = Counter()
    covered: dict[str, set] = defaultdict(set)
    for f in files:
        for author, n in file_authors.get(f, {}).items():
            totals[author] += n
            covered[author].add(f)
    ranked = sorted(totals, key=lambda a: (-len(covered[a]), -totals[a], a))[:limit]
    return [{"author": a, "files_covered": len(covered[a]), "commits": totals[a], "files": sorted(covered[a])[:5]}
            for a in ranked]
