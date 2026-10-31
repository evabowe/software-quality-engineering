"""Tests für das Starten von Ollama in Colab (Subprozesse und HTTP durch Fakes ersetzt)."""

import subprocess

import pytest

from judge_lab import ollama_colab


class Recorder:
    def __init__(self, result=None, exc=None):
        self.calls = []
        self.result = result
        self.exc = exc

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.exc:
            raise self.exc
        return self.result


def test_ensure_gpu_true_when_nvidia_smi_works():
    assert ollama_colab.ensure_gpu(run=Recorder(subprocess.CompletedProcess([], 0))) is True


def test_ensure_gpu_false_without_driver():
    assert ollama_colab.ensure_gpu(run=Recorder(exc=FileNotFoundError())) is False
    assert ollama_colab.ensure_gpu(run=Recorder(subprocess.CompletedProcess([], 9))) is False


def test_install_idempotent():
    run = Recorder()
    assert ollama_colab.install(run=run, which=lambda name: "/usr/local/bin/ollama") is False
    assert run.calls == []


def test_install_runs_official_installer():
    run = Recorder(subprocess.CompletedProcess([], 0))
    assert ollama_colab.install(run=run, which=lambda name: None) is True
    (command,), kwargs = run.calls[0]
    assert "https://ollama.com/install.sh" in " ".join(command)
    assert kwargs["check"] is True


def test_serve_not_started_twice(tmp_path):
    popen = Recorder()
    assert ollama_colab.serve(popen=popen, is_up=lambda: True, log_path=tmp_path / "log") is False
    assert popen.calls == []


def test_serve_starts_and_waits(tmp_path):
    states = iter([False, False, True])
    popen = Recorder()
    started = ollama_colab.serve(popen=popen, is_up=lambda: next(states), log_path=tmp_path / "log",
                                 sleep=lambda s: None)
    assert started is True
    (command,), _ = popen.calls[0]
    assert command == ["ollama", "serve"]


def test_serve_timeout_raises(tmp_path):
    with pytest.raises(RuntimeError, match="Ollama"):
        ollama_colab.serve(popen=Recorder(), is_up=lambda: False, log_path=tmp_path / "log",
                           sleep=lambda s: None, wait_s=3)


def test_no_gpu_message_skips_install():
    run = Recorder(exc=FileNotFoundError())
    message = ollama_colab.start_local_model("qwen2.5-coder:3b", run=run)
    assert "GPU" in message and "Fallback" in message
    assert len(run.calls) == 1  # nur nvidia-smi, keine Installation


def test_serve_sets_context_length(tmp_path):
    # Mit dem Standard-Kontext (2–4k Tokens) würde Ollama den System-Prompt mit der Haltung abschneiden.
    states = iter([False, True])
    popen = Recorder()
    ollama_colab.serve(popen=popen, is_up=lambda: next(states), log_path=tmp_path / "log", sleep=lambda s: None)
    _, kwargs = popen.calls[0]
    assert int(kwargs["env"]["OLLAMA_CONTEXT_LENGTH"]) >= 8192
    assert "PATH" in kwargs["env"]
