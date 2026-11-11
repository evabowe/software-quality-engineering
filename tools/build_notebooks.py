"""Erzeugt notebooks/hands_on_gpu.ipynb aus notebooks/hands_on.ipynb (Gruppe 4, lokales Modell).

Gleicher Inhalt, nur die Colab-Metadaten fordern eine T4-GPU an – so muss Gruppe 4 den
Laufzeittyp nicht von Hand umstellen. Nach jeder Änderung an hands_on.ipynb ausführen:

    python tools/build_notebooks.py
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

NOTEBOOKS = Path(__file__).resolve().parent.parent / "notebooks"


def build_gpu_notebook(notebook: dict) -> dict:
    gpu = copy.deepcopy(notebook)
    gpu["metadata"]["accelerator"] = "GPU"
    gpu["metadata"].setdefault("colab", {})["gpuType"] = "T4"
    return gpu


def main() -> None:
    plain = json.loads((NOTEBOOKS / "hands_on.ipynb").read_text(encoding="utf-8"))
    target = NOTEBOOKS / "hands_on_gpu.ipynb"
    target.write_text(json.dumps(build_gpu_notebook(plain), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"geschrieben: {target}")


if __name__ == "__main__":
    main()
