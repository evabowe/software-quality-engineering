"""Tests für tools/compute_complexity.py."""

from judge_lab.config import SNIPPETS_DIR
from tools.compute_complexity import measure, update_meta

META = """# Kommentar oben
id: demo
complexity:
  level: L2                 # manuell gesetzt
  cognitive: null           # wird gesetzt
  loc: 14
defects:
  - id: D1
"""


def test_update_meta_preserves_other_lines(tmp_path):
    path = tmp_path / "meta.yaml"
    path.write_text(META)
    update_meta(path, {"cognitive": 3, "loc": 8})
    assert path.read_text() == META.replace(
        "  cognitive: null           # wird gesetzt", "  cognitive: 3"
    ).replace("  loc: 14", "  loc: 8")


def test_measure_bank_account():
    # Wert laut Konzept (complexipy) für bank_account.py
    assert measure(SNIPPETS_DIR / "bank_account")["cognitive"] == 9


def test_measure_counts_non_blank_lines(tmp_path):
    (tmp_path / "meta.yaml").write_text("code_file: f.py\n")
    (tmp_path / "f.py").write_text("def f():\n\n    return 1\n\n")
    assert measure(tmp_path)["loc"] == 2
