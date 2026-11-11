"""Vertrag zwischen Python-Client und Apps Script: gleiche Felder, gleiche Punkte."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from judge_lab.config import POINTS
from judge_lab.scoreboard import RECORD_FIELDS

SCOREBOARD_DIR = Path(__file__).parent.parent / "scoreboard"
CODE_GS = (SCOREBOARD_DIR / "Code.gs").read_text(encoding="utf-8")


def _js_constant(name):
    match = re.search(rf"const {name} = (\[.*?\]|\{{.*?\}});", CODE_GS, re.DOTALL)
    assert match, f"{name} nicht in Code.gs gefunden"
    literal = re.sub(r"//.*", "", match.group(1))
    literal = re.sub(r"(\w+):", r'"\1":', literal) if literal.startswith("{") else literal
    return json.loads(literal.replace("'", '"').replace(",\n]", "\n]").replace(",]", "]"))


def test_fields_match():
    assert tuple(_js_constant("FIELDS")) == RECORD_FIELDS


def test_points_match():
    assert _js_constant("POINTS") == POINTS


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js nicht installiert")
def test_aggregation_node_tests():
    result = subprocess.run(
        ["node", "--test", str(SCOREBOARD_DIR / "aggregate.test.mjs")], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout[-2000:]


def test_strict_vs_lenient_options_match():
    # Das Dashboard vergleicht Prognosen wörtlich mit diesen Texten.
    from judge_lab.ui import STRICT_VS_LENIENT_OPTIONS

    assert tuple(_js_constant("STRICT_VS_LENIENT")) == STRICT_VS_LENIENT_OPTIONS


def test_groups_match():
    from judge_lab.config import GROUPS

    assert tuple(_js_constant("GROUP_NAMES")) == tuple(GROUPS)
