"""Tests für tools/import_quixbugs.py."""

import hashlib
import json

import yaml

from tools.import_quixbugs import import_program, render_tests

QUICKSORT_CASES = [
    [[[1, 2, 6, 72, 7, 33, 4]], [1, 2, 4, 6, 7, 33, 72]],
    [[[5, 4, 3, 2, 1]], [1, 2, 3, 4, 5]],
    [[[3, 1, 4, 1]], [1, 1, 3, 4]],
    [[[2]], [2]],
    [[[]], []],
    [[[9, 8]], [8, 9]],
    [[[7, 7]], [7, 7]],
]


def test_render_tests_quicksort():
    text = render_tests("quicksort", QUICKSORT_CASES)
    assert "from quicksort import quicksort" in text
    assert "assert quicksort([1, 2, 6, 72, 7, 33, 4]) == [1, 2, 4, 6, 7, 33, 72]" in text
    # Nur die ersten 6 Fälle
    assert text.count("def test_case_") == 6
    assert "[7, 7]" not in text


def test_render_tests_multiple_args():
    text = render_tests("levenshtein", [[["electron", "neutron"], 3]])
    assert "assert levenshtein('electron', 'neutron') == 3" in text


def test_rendered_tests_are_valid_python():
    compile(render_tests("quicksort", QUICKSORT_CASES), "tests.py", "exec")


def _fake_checkout(root, name, code):
    (root / "python_programs").mkdir(parents=True)
    (root / "json_testcases").mkdir()
    (root / "python_programs" / f"{name}.py").write_bytes(code)
    lines = [json.dumps([[1], 1]), json.dumps([[2], 1])]
    (root / "json_testcases" / f"{name}.json").write_text("\n".join(lines) + "\n")


def test_import_creates_skeleton(tmp_path):
    code = b'\ndef foo(n):\n    return 1\n\n"""\nFoo Function\nfoo\n"""\n'
    _fake_checkout(tmp_path / "qb", "foo", code)
    folder = import_program(tmp_path / "qb", "foo", tmp_path / "snippets", commit="abc123")

    assert (folder / "foo.py").read_bytes() == code
    meta = yaml.safe_load((folder / "meta.yaml").read_text())
    assert meta["id"] == "qb_foo"
    assert meta["title"] == "Foo Function"
    assert meta["spec"] == "trailing_string"
    assert meta["source"]["commit"] == "abc123"
    assert meta["source"]["sha256"] == hashlib.sha256(code).hexdigest()
    assert "assert foo(1) == 1" in (folder / "tests.py").read_text()


def test_import_keeps_existing_defects(tmp_path):
    code = b"def foo(n):\n    return 1\n"
    _fake_checkout(tmp_path / "qb", "foo", code)
    folder = import_program(tmp_path / "qb", "foo", tmp_path / "snippets", commit="old")
    meta_path = folder / "meta.yaml"
    meta_path.write_text(
        meta_path.read_text() + "  - id: D1  # manuell gepflegt\n    kind: bug\n",
    )

    import_program(tmp_path / "qb", "foo", tmp_path / "snippets", commit="new")

    text = meta_path.read_text()
    assert "# manuell gepflegt" in text
    assert yaml.safe_load(text)["source"]["commit"] == "new"


def test_render_tests_skips_cases_quixbugs_skips():
    # QuixBugs überspringt diesen Fall selbst, weil die naive Rekursion zu lange läuft.
    slow = ["amanaplanacanalpanama", "docnoteidissentafastneverpreventsafatnessidietoncod"]
    cases = [[["a", "b"], 1], [slow, 42]] + [[["x" * n, ""], n] for n in range(1, 6)]
    text = render_tests("levenshtein", cases)
    assert "amanaplanacanalpanama" not in text
    assert text.count("def test_case_") == 6


def test_rendered_tests_do_not_name_the_benchmark():
    text = render_tests("quicksort", QUICKSORT_CASES).lower()
    assert "quixbugs" not in text and "json_testcases" not in text
