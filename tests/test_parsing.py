"""Tests für das tolerante Parsen der LLM-Antworten."""

import json

import pytest

from judge_lab.parsing import ParseError, extract_json, parse_verdict

VALID = {
    "findings": [
        {
            "line_start": 7,
            "line_end": 7,
            "category": "bug",
            "severity": "high",
            "description": "drops duplicates",
            "suggested_fix": "if x >= pivot",
        }
    ],
    "scores": {"functional_correctness": 4, "reliability": 6, "maintainability": 7, "readability": 8},
    "overall_score": 5.6,
}


def test_plain_json():
    verdict = parse_verdict(json.dumps(VALID), line_count=19)
    assert verdict.findings[0].line_start == 7
    assert verdict.findings[0].category == "bug"
    assert verdict.scores["readability"] == 8
    assert verdict.overall_score == 5.6


def test_markdown_fence():
    text = "Here is my review:\n```json\n" + json.dumps(VALID) + "\n```\nThanks!"
    assert extract_json(text) == VALID


def test_think_block_removed():
    text = "<think>The dict {a: 1} looks odd</think>\n" + json.dumps(VALID)
    assert extract_json(text) == VALID


def test_braces_inside_strings():
    data = {"findings": [{"line_start": 3, "category": "style", "description": "use {} or {'+': 1}"}]}
    text = "Sure. " + json.dumps(data) + " Let me know if you need more {details}."
    assert extract_json(text) == data


def test_escaped_quotes_inside_strings():
    data = {"findings": [{"line_start": 3, "category": "bug", "description": 'say \\"} hi'}]}
    assert extract_json(json.dumps(data)) == data


def test_string_numbers_and_ranges():
    data = {
        "findings": [
            {"line_start": "7", "line_end": "9", "category": "bug"},
            {"line_start": "12-14", "category": "bug"},
            {"line_start": None, "category": "bug"},
        ]
    }
    verdict = parse_verdict(json.dumps(data), line_count=20)
    assert [(f.line_start, f.line_end) for f in verdict.findings] == [(7, 9), (12, 14)]


def test_missing_line_end_defaults_to_start():
    verdict = parse_verdict('{"findings": [{"line_start": 5, "category": "bug"}]}', line_count=10)
    assert verdict.findings[0].line_end == 5


def test_swapped_and_out_of_range_lines():
    verdict = parse_verdict('{"findings": [{"line_start": 12, "line_end": 3, "category": "bug"}]}', line_count=10)
    assert (verdict.findings[0].line_start, verdict.findings[0].line_end) == (3, 10)


def test_line_zero_clamped_to_one():
    verdict = parse_verdict('{"findings": [{"line_start": 0, "category": "bug"}]}', line_count=10)
    assert verdict.findings[0].line_start == 1


def test_scores_clamped_and_parsed():
    data = {"scores": {"functional_correctness": 15, "reliability": "8/10", "maintainability": -2,
                       "readability": "7", "creativity": 9}, "overall_score": "6.5"}
    verdict = parse_verdict(json.dumps(data), line_count=10)
    assert verdict.scores == {"functional_correctness": 10, "reliability": 8, "maintainability": 0, "readability": 7}
    assert verdict.overall_score == 6.5


@pytest.mark.parametrize(
    "raw, expected",
    [("Bug", "bug"), ("correctness", "bug"), ("Logic", "bug"), ("security", "robustness"),
     ("reliability", "robustness"), ("readability", "style"), ("naming", "style"),
     ("design", "maintainability"), (None, "maintainability")],
)
def test_category_synonyms(raw, expected):
    data = {"findings": [{"line_start": 1, "category": raw}]}
    assert parse_verdict(json.dumps(data), line_count=5).findings[0].category == expected


def test_unknown_severity_defaults_to_medium():
    data = {"findings": [{"line_start": 1, "category": "bug", "severity": "critical!"}]}
    assert parse_verdict(json.dumps(data), line_count=5).findings[0].severity == "medium"


def test_missing_fields_defaults():
    verdict = parse_verdict("{}", line_count=5)
    assert verdict.findings == [] and verdict.scores == {} and verdict.overall_score is None


def test_findings_not_a_list_raises():
    with pytest.raises(ParseError):
        parse_verdict('{"findings": "none found"}', line_count=5)


@pytest.mark.parametrize("text", ["", "I could not review this code.", "{broken json", "[1, 2, 3]"])
def test_garbage_raises(text):
    with pytest.raises(ParseError):
        parse_verdict(text, line_count=5)
