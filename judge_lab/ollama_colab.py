"""Ollama in Google Colab installieren, starten und ein Modell laden (nur Gruppe 4).

Alle Schritte sind idempotent: Die Zelle darf mehrfach ausgeführt werden, ohne dass
Ollama doppelt installiert oder ein zweiter Server gestartet wird. Abhängigkeiten zu
Subprozessen und HTTP werden für die Tests als Parameter übergeben.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import requests

from judge_lab.config import MODELS, OLLAMA_BASE_URL
from judge_lab.llm import ChatClient, LLMResult

INSTALL_COMMAND = "curl -fsSL https://ollama.com/install.sh | sh"
VERSION_URL = OLLAMA_BASE_URL.replace("/v1", "/api/version")


def _default_log_path() -> Path:
    colab = Path("/content")
    return (colab if colab.is_dir() else Path(tempfile.gettempdir())) / "ollama.log"


def ensure_gpu(run=subprocess.run) -> bool:
    """True, wenn eine NVIDIA-GPU verfügbar ist (Colab: Laufzeittyp T4)."""
    try:
        return run(["nvidia-smi"], capture_output=True).returncode == 0
    except (FileNotFoundError, OSError):
        return False


def install(run=subprocess.run, which=shutil.which) -> bool:
    """Installiert Ollama mit dem offiziellen Installer; False, wenn es schon da ist."""
    if which("ollama"):
        return False
    run(["bash", "-c", INSTALL_COMMAND], check=True)
    return True


def is_up(get=requests.get) -> bool:
    try:
        return get(VERSION_URL, timeout=2).status_code == 200
    except requests.RequestException:
        return False


def serve(popen=subprocess.Popen, is_up=is_up, log_path: Path | None = None, wait_s: int = 30,
          sleep=time.sleep) -> bool:
    """Startet ``ollama serve`` im Hintergrund; False, wenn der Server schon läuft."""
    if is_up():
        return False
    log = open(log_path or _default_log_path(), "a", encoding="utf-8")  # bleibt für den Server offen
    popen(["ollama", "serve"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(wait_s):
        if is_up():
            return True
        sleep(1)
    raise RuntimeError(f"Ollama-Server antwortet nicht nach {wait_s} s. Details im Log: {log.name}")


def pull(model: str, run=subprocess.run) -> None:
    """Lädt das Modell; die Fortschrittsanzeige von ``ollama pull`` erscheint direkt in der Zelle."""
    run(["ollama", "pull", model], check=True)


def warmup(model: str) -> LLMResult:
    """Eine Mini-Anfrage, damit das Modell vor Auftrag 1 im GPU-Speicher liegt."""
    client = ChatClient(OLLAMA_BASE_URL, "ollama", model, provider="ollama", timeout_s=300, max_retries=0)
    return client.complete([{"role": "user", "content": 'Reply with the JSON object {"ok": true}.'}])


def start_local_model(model: str = MODELS["local"]["id"], run=subprocess.run) -> str:
    """Alle Schritte nacheinander; gibt eine Statusmeldung für das Notebook zurück."""
    if not ensure_gpu(run=run):
        return (
            "⚠️ Keine GPU gefunden. Entweder Laufzeit → Laufzeittyp ändern → T4-GPU und diese Zelle erneut "
            "ausführen, oder im Setup „Gruppe 4 – Fallback ohne GPU“ wählen (kleines Modell über OpenRouter)."
        )
    install(run=run)
    serve()
    pull(model, run=run)
    result = warmup(model)
    if result.error:
        return f"⚠️ Modell geladen, aber die Testanfrage ist fehlgeschlagen: {result.error}"
    return f"✅ Lokales Modell bereit: {model} (Testanfrage {result.latency_s:.0f} s)"
