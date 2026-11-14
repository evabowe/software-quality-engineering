"""Tests für den Judge-Aufruf mit Reparatur-Versuch."""

import json

from judge_lab.llm import LLMResult
from judge_lab.parsing import REPAIR_MESSAGE
from judge_lab.prompts import build_prompt
from judge_lab.runner import judge
from judge_lab.snippets import get_snippet

VALID = json.dumps({"findings": [{"line_start": 26, "category": "bug"}],
                    "scores": {"functional_correctness": 4, "reliability": 5, "maintainability": 6, "readability": 7}})
SNIPPET = get_snippet("bank_account")
MESSAGES = build_prompt(SNIPPET, custom_block="Sei streng.", with_tests=False)


class ScriptedClient:
    """Liefert nacheinander die vorgegebenen Antworten; merkt sich alle Aufrufe."""

    provider = "mock"
    model_id = "scripted"

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        answer = self.answers.pop(0)
        return answer if isinstance(answer, LLMResult) else LLMResult(answer, 0.5, 100, 20)


def test_repair_retry_used_once():
    client = ScriptedClient("Sorry, here it is: {broken", VALID)
    verdict, result, repaired = judge(client, MESSAGES, SNIPPET.line_count)
    assert verdict is not None and verdict.findings[0].line_start == 26
    assert repaired is True and len(client.calls) == 2
    assert client.calls[1][-1] == {"role": "user", "content": REPAIR_MESSAGE}
    assert client.calls[1][-2]["role"] == "assistant"
    assert (result.latency_s, result.tokens_in, result.tokens_out) == (1.0, 200, 40)


def test_repair_fails_gives_none():
    client = ScriptedClient("nope", "still nope")
    verdict, _, repaired = judge(client, MESSAGES, SNIPPET.line_count)
    assert verdict is None and repaired is True and len(client.calls) == 2


def test_llm_error_is_not_counted_as_judge_result():
    # Ein Transportfehler (Key, Limit, Ausfall) sagt nichts über den Judge: kein Urteil, kein Reparatur-Versuch.
    client = ScriptedClient(LLMResult("", 1.0, None, None, error="LLM-Aufruf fehlgeschlagen: 429"))
    verdict, result, repaired = judge(client, MESSAGES, SNIPPET.line_count)
    assert verdict is None and "429" in result.error and repaired is False
    assert len(client.calls) == 1
