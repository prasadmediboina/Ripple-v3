"""Impact benchmark. Case = <name>-base/, <name>-head/, <name>-expected.json (human-verified truth).

Add real open-source change cases here BEFORE making any accuracy claim. This starter case is
self-authored, so a perfect score proves the harness works, not that the product is accurate.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))
from app.engine import analyze_snapshots  # noqa: E402

ROOT = pathlib.Path(__file__).parent / "cases"


def load(d, prefix):
    return {prefix + p.relative_to(d).as_posix(): p.read_text() for p in d.rglob("*.py")}


def main() -> int:
    tp = fp = fn = ttp = tfn = 0
    for exp_file in sorted(ROOT.glob("*-expected.json")):
        name = exp_file.name.removesuffix("-expected.json")
        exp = json.loads(exp_file.read_text())
        r = analyze_snapshots(load(ROOT / f"{name}-base", exp["prefix"]), load(ROOT / f"{name}-head", exp["prefix"]))
        got, want = {f.affected_name for f in r.findings}, set(exp["affected"])
        tp += len(got & want); fp += len(got - want); fn += len(want - got)
        got_t, want_t = {t.test_name for t in r.tests}, set(exp["tests"])
        ttp += len(got_t & want_t); tfn += len(want_t - got_t)
        print(f"{name}: precision={len(got & want) / max(1, len(got)):.2f} recall={len(got & want) / max(1, len(want)):.2f}")
    print(f"OVERALL impact precision={tp / max(1, tp + fp):.2f} recall={tp / max(1, tp + fn):.2f} | test recall={ttp / max(1, ttp + tfn):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
