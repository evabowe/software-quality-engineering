"""Strukturprüfung der Notebooks (ausgeführt werden sie manuell mit dem Modell „mock“)."""

import json
import re
from pathlib import Path

import pytest

NOTEBOOKS = Path(__file__).parent.parent / "notebooks"


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
        assert not re.search(r"sk-or-[A-Za-z0-9]", source), "API-Key im Notebook"


def test_hands_on_follows_cell_plan():
    notebook = json.loads((NOTEBOOKS / "hands_on.ipynb").read_text(encoding="utf-8"))
    code = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    for call in ("ui.setup_panel()", "ollama_colab.start_local_model()", "ui.prognosis_panel()",
                 "ui.snippet_viewer()", "ui.assignment1_panel()", "ui.assignment2_panel()"):
        assert call in code
    # Die Lösung darf im Studierenden-Notebook nicht vorkommen.
    assert "instructor" not in code and "SOLUTION" not in code
