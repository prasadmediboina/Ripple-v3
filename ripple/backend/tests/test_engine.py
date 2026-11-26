from app.engine import analyze_snapshots
from app.engine.graph import build_graph


def modified(files, path, old, new):
    h = dict(files)
    assert old in h[path]
    h[path] = h[path].replace(old, new)
    return h


def test_formatting_and_comment_changes_are_not_changes(shop_files):
    head = modified(shop_files, "shop/payments.py", "if order_total <= 0:", "# note\n    if order_total   <=  0:")
    r = analyze_snapshots(shop_files, head)
    assert r.changes == []


def test_payment_change_finds_dependents_with_evidence(shop_files):
    head = modified(shop_files, "shop/payments.py", '"status": "paid"', '"status": "ok"')
    r = analyze_snapshots(shop_files, head)
    assert [c.name for c in r.changes] == ["process_payment"]
    names = {f.affected_name: f for f in r.findings}
    assert {"create_order", "checkout", "refund", "Gateway.charge"} <= set(names)
    direct = names["create_order"]
    assert direct.depth == 1 and direct.confidence == "high"
    assert "shop/orders.py" in direct.path[0].evidence
    assert names["checkout"].depth == 2 and names["checkout"].confidence == "medium"
    assert all(f.status == "potential_impact" for f in r.findings)


def test_relative_imports_resolve(shop_files):
    g = build_graph(shop_files)
    assert any(e.source_id == "shop/refunds.py::refund" and e.target_id == "shop/payments.py::process_payment"
               for e in g.edges)


def test_test_selection_and_gaps(shop_files):
    head = modified(shop_files, "shop/payments.py", '"status": "paid"', '"status": "ok"')
    r = analyze_snapshots(shop_files, head)
    assert [t.test_name for t in r.tests] == ["test_checkout_paid"]
    gap_names = {g.split("::")[1] for g in r.coverage_gaps}
    assert "refund" in gap_names           # no test reaches refund()
    assert "create_order" not in gap_names


def test_unknowns_surface_dynamic_calls(shop_files):
    head = modified(shop_files, "shop/notifications.py", "return handler()", "return handler() or None")
    r = analyze_snapshots(shop_files, head)
    assert any("handler" in u for u in r.unknowns)


def test_removed_function_uses_base_graph(shop_files):
    head = dict(shop_files)
    head["shop/payments.py"] = head["shop/payments.py"].split("class Gateway")[0].replace("def process_payment", "def renamed_payment")
    r = analyze_snapshots(shop_files, head)
    kinds = {c.name: c.kind for c in r.changes}
    assert kinds["process_payment"] == "removed"
    assert "create_order" in {f.affected_name for f in r.findings}


def test_syntax_errors_and_other_languages_are_reported_not_hidden(shop_files):
    head = dict(shop_files)
    head["shop/broken.py"] = "def x(:\n"
    head["web/app.ts"] = "export const a = 1"
    r = analyze_snapshots(shop_files, head)
    assert any("broken.py" in u for u in r.unknowns)
    assert "web/app.ts" in r.not_analyzed


def test_markdown_report_renders(shop_files):
    head = modified(shop_files, "shop/payments.py", '"status": "paid"', '"status": "ok"')
    md = analyze_snapshots(shop_files, head).to_markdown()
    assert "Potential impacts" in md and "not confirmed defects" in md
