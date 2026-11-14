"""Tests für den OpenAI-kompatiblen Client und den Mock-Provider."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from judge_lab import config
from judge_lab.llm import ChatClient, ConfigError, MockClient, make_client
from judge_lab.matching import match_findings
from judge_lab.parsing import ParseError, parse_verdict
from judge_lab.prompts import build_prompt
from judge_lab.snippets import get_snippet, load_snippets

COMPLETION = {
    "id": "x", "object": "chat.completion", "created": 0, "model": "m",
    "choices": [{"index": 0, "finish_reason": "stop",
                 "message": {"role": "assistant", "content": '{"findings": []}'}}],
    "usage": {"prompt_tokens": 11, "completion_tokens": 5, "total_tokens": 16},
}


@pytest.fixture
def fake_api():
    """Lokaler HTTP-Server, der Chat-Completions mit vorgegebenen Antworten beantwortet."""
    state = {"responses": [], "requests": []}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            state["requests"].append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "json": json.loads(body)})
            status, payload = state["responses"].pop(0)
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    state["base_url"] = f"http://127.0.0.1:{server.server_address[1]}/v1"
    yield state
    server.shutdown()


def _client(base_url, **kwargs):
    return ChatClient(base_url, "test-key", "vendor/model", provider="openrouter", timeout_s=5, **kwargs)


def test_complete_success(fake_api):
    fake_api["responses"].append((200, COMPLETION))
    result = _client(fake_api["base_url"]).complete([{"role": "user", "content": "hi"}])

    assert result.error is None
    assert result.text == '{"findings": []}'
    assert (result.tokens_in, result.tokens_out) == (11, 5)
    request = fake_api["requests"][0]
    assert request["path"] == "/v1/chat/completions"
    assert request["headers"]["authorization"] == "Bearer test-key"
    assert request["json"]["model"] == "vendor/model"
    assert request["json"]["temperature"] == 0
    assert request["json"]["max_tokens"] == config.MAX_TOKENS
    assert request["json"]["response_format"] == {"type": "json_object"}


def test_server_error_becomes_error_result(fake_api):
    fake_api["responses"].append((500, {"error": {"message": "boom"}}))
    result = _client(fake_api["base_url"], max_retries=0).complete([{"role": "user", "content": "hi"}])
    assert result.text == ""
    assert result.error and "500" in result.error


def test_unreachable_server_becomes_error_result():
    result = _client("http://127.0.0.1:9/v1", max_retries=0).complete([{"role": "user", "content": "hi"}])
    assert result.error


def test_make_client_any_openrouter_id():
    client = make_client("openai/gpt-6-luna", "sk-test")
    assert client.provider == "openrouter" and client.model_id == "openai/gpt-6-luna"


def test_make_client_mock_needs_no_key():
    assert make_client("mock", None).model_id == "mock"


def test_make_client_missing_key():
    with pytest.raises(ConfigError, match="verbinde"):
        make_client("openai/gpt-6-luna", "")


def _mock_answer(snippet_id, attitude="objective"):
    snippet = get_snippet(snippet_id)
    client = MockClient(load_snippets())
    return snippet, client.complete(build_prompt(snippet, attitude=attitude, with_tests=False))


def test_mock_deterministic_and_parsable():
    snippet, first = _mock_answer("bank_account")
    _, second = _mock_answer("bank_account")
    assert first == second
    verdict = parse_verdict(first.text, snippet.line_count)
    result = match_findings(verdict.findings, snippet.defects)
    assert result.tp >= 1 and result.fp >= 1


def test_mock_scores_depend_on_attitude():
    snippet, strict = _mock_answer("qb_quicksort", "strict")
    _, lenient = _mock_answer("qb_quicksort", "lenient")
    strict_scores = parse_verdict(strict.text, snippet.line_count).scores
    lenient_scores = parse_verdict(lenient.text, snippet.line_count).scores
    assert strict_scores["functional_correctness"] < lenient_scores["functional_correctness"]


def test_mock_wraps_shunting_yard_in_prose():
    snippet, answer = _mock_answer("qb_shunting_yard")
    assert answer.text.lstrip().startswith("Here")
    parse_verdict(answer.text, snippet.line_count)


def test_mock_broken_json_for_levenshtein():
    snippet, answer = _mock_answer("qb_levenshtein")
    with pytest.raises(ParseError):
        parse_verdict(answer.text, snippet.line_count)


def test_mock_descriptions_reveal_no_ground_truth():
    for snippet in load_snippets():
        answer = MockClient(load_snippets()).complete(build_prompt(snippet, attitude="strict", with_tests=True))
        for defect in snippet.defects:
            assert defect.description not in answer.text
