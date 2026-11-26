import pathlib, pytest

FIX = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def shop_files():
    out = {}
    for p in FIX.rglob("*.py"):
        out[p.relative_to(FIX).as_posix()] = p.read_text()
    return out
