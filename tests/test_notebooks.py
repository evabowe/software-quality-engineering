"""Strukturprüfung der Notebooks (ausgeführt werden sie manuell mit dem Modell „mock“)."""

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
NOTEBOOKS = REPO / "notebooks"
API_KEY = re.compile(r"sk-or-[A-Za-z0-9]")


@pytest.mark.parametrize("name", ["hands_on.ipynb", "instructor.ipynb"])
def test_notebooks_valid(name):
    notebook = json.loads((NOTEBOOKS / name).read_text(encoding="utf-8"))
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    assert code_cells
    for cell in code_cells:
        source = "".join(cell["source"])
        assert source.startswith("#@title "), source[:60]
        assert cell["metadata"].get("cellView") == "form"
        assert cell["outputs"] == [] and cell["execution_count"] is None
        assert not API_KEY.search(source), "API-Key im Notebook"


def test_hands_on_has_one_markdown_and_one_start_cell():
    notebook = json.loads((NOTEBOOKS / "hands_on.ipynb").read_text(encoding="utf-8"))
    welcome, start = notebook["cells"]
    assert welcome["cell_type"] == "markdown" and "Trotzdem ausführen" in "".join(welcome["source"])
    code = "".join(start["source"])
    assert start["cell_type"] == "code" and start["metadata"].get("cellView") == "form"
    assert code.startswith("#@title ▶ Start – hier klicken")
    assert "from judge_lab import app" in code and "app.show()" in code
    # Erneutes Ausführen: kein zweiter Klon, keine zweite Installation.
    assert "if not os.path.isdir(REPO_DIR)" in code and "INSTALLED_MARK" in code
    # Die Lösung darf im Studierenden-Notebook nicht vorkommen.
    assert "instructor" not in code and "SOLUTION" not in code


def test_no_api_keys_in_repository():
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=REPO,
                           capture_output=True, text=True, check=True).stdout.split()
    leaks = []
    for name in files:
        path = REPO / name
        if not path.is_file() or name.endswith("test_notebooks.py"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if API_KEY.search(text):
            leaks.append(name)
    assert leaks == []
