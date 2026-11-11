"""Ausführung der Judge-Läufe: einzelner Lauf, Matrix (Auftrag 1) und Prompt-Challenge (Auftrag 2).

Jeder Lauf erzeugt genau einen Datensatz mit allen Feldern aus ``RECORD_FIELDS`` und
übergibt ihn sofort an ``RunContext.sink`` (in der Session: ``Scoreboard.submit``).
Fehler einzelner Läufe brechen nichts ab; sie werden im Datensatz markiert.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone

from judge_lab import NOTEBOOK_VERSION
from judge_lab.config import ATTITUDES, CONCURRENCY, FINDINGS_JSON_MAX, HUMAN_SNIPPET, LOCAL_ATTITUDES, MODELS
from judge_lab.llm import LLMResult
from judge_lab.matching import match_findings
from judge_lab.parsing import REPAIR_MESSAGE, JudgeVerdict, ParseError, parse_verdict
from judge_lab.prompts import build_prompt, load_attitude, prompt_hash
from judge_lab.scoreboard import RECORD_FIELDS
from judge_lab.scoring import weighted_score
from judge_lab.snippets import Snippet, load_snippets

Progress = Callable[[int, int], None]


@dataclass(frozen=True)
class RunContext:
    group: str
    model_key: str  # Modell der Gruppe
    session_id: str
    sink: Callable[[dict], object]


def _combine(first: LLMResult, second: LLMResult) -> LLMResult:
    def total(a, b):
        return None if a is None and b is None else (a or 0) + (b or 0)

    return LLMResult(
        text=second.text,
        latency_s=first.latency_s + second.latency_s,
        tokens_in=total(first.tokens_in, second.tokens_in),
        tokens_out=total(first.tokens_out, second.tokens_out),
        error=second.error,
    )


def judge(client, messages: list[dict], line_count: int) -> tuple[JudgeVerdict | None, LLMResult, bool]:
    """Fragt den Judge; bei unlesbarer Antwort genau ein Reparatur-Versuch.

    Rückgabe: (Urteil oder None, zusammengefasstes LLM-Ergebnis, ob repariert wurde)
    """
    result = client.complete(messages)
    if result.error:
        return None, result, False
    try:
        return parse_verdict(result.text, line_count), result, False
    except ParseError:
        pass
    repair = messages + [
        {"role": "assistant", "content": result.text},
        {"role": "user", "content": REPAIR_MESSAGE},
    ]
    combined = _combine(result, client.complete(repair))
    if combined.error:
        return None, combined, True
    try:
        return parse_verdict(combined.text, line_count), combined, True
    except ParseError:
        return None, combined, True


def _empty_record(ctx: RunContext, phase: str) -> dict:
    record = dict.fromkeys(RECORD_FIELDS, "")
    record.update(
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        run_id=uuid.uuid4().hex,
        session_id=ctx.session_id,
        group=ctx.group,
        phase=phase,
        notebook_version=NOTEBOOK_VERSION,
    )
    return record


def run_one(
    ctx: RunContext,
    client,
    snippet: Snippet,
    *,
    phase: str,
    with_tests: bool,
    attitude: str | None = None,
    custom_block: str | None = None,
    submission_no: int | None = None,
    submission_id: str = "",
    model_key: str | None = None,
) -> dict:
    """Ein Judge-Lauf auf einem Snippet; gibt den (bereits gesendeten) Datensatz zurück."""
    record = _empty_record(ctx, phase)
    block = custom_block if custom_block is not None else load_attitude(attitude)
    record.update(
        model_key=model_key or ctx.model_key,
        model_id=client.model_id,
        attitude=attitude or "custom",
        snippet_id=snippet.id,
        complexity_level=snippet.level or "",
        with_tests=with_tests,
        prompt_hash=prompt_hash(block),
        prompt_text=custom_block if phase == "a2_submit" else "",
        submission_no=submission_no if submission_no is not None else "",
        submission_id=submission_id,
    )
    verdict, error, infrastructure_failed = None, "", False
    try:
        messages = build_prompt(snippet, attitude=attitude, custom_block=custom_block, with_tests=with_tests)
        verdict, result, _ = judge(client, messages, snippet.line_count)
        infrastructure_failed = bool(result.error)
        error = result.error or ("" if verdict else "Antwort war kein lesbares JSON (auch nach Reparatur-Versuch).")
        record.update(latency_s=round(result.latency_s, 2), tokens_in=result.tokens_in, tokens_out=result.tokens_out)
    except Exception as exc:  # noqa: BLE001 – ein kaputter Lauf darf die Matrix nicht abbrechen
        infrastructure_failed, error = True, f"{type(exc).__name__}: {exc}"

    if infrastructure_failed:
        # Key, Limit, Netz oder Server: Das sagt nichts über den Judge. Metriken bleiben leer
        # (parse_ok=None), damit Dashboard und Tabelle den Lauf nicht als „0 gefunden“ werten.
        record.update(n_defects=len(snippet.defects), parse_ok=None, error=error,
                      tp=None, fp=None, neutral=None, recall=None, precision=None)
        ctx.sink(record)
        return record

    findings = verdict.findings if verdict else []
    match = match_findings(findings, snippet.defects)
    record.update(
        tp=match.tp,
        fp=match.fp,
        neutral=match.neutral,
        n_defects=match.n_defects,
        recall=match.recall,
        precision=match.precision,
        weighted_score=weighted_score(verdict.scores) if verdict else None,
        llm_overall_score=verdict.overall_score if verdict else None,
        scores_json=json.dumps(verdict.scores) if verdict else "",
        found_defect_ids=",".join(match.found_defect_ids),
        findings_json=json.dumps([f.model_dump() for f in findings], ensure_ascii=False)[:FINDINGS_JSON_MAX],
        parse_ok=verdict is not None,
        error=error,
    )
    ctx.sink(record)
    return record


def _run_parallel(jobs: list[Callable[[], dict]], workers: int, on_progress: Progress | None, offset: int = 0,
                  total: int | None = None) -> list[dict]:
    total = total if total is not None else len(jobs)
    results: list[dict | None] = [None] * len(jobs)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(job): index for index, job in enumerate(jobs)}
        for done, future in enumerate(as_completed(futures), start=1):
            results[futures[future]] = future.result()
            if on_progress:
                on_progress(offset + done, total)
    return results  # type: ignore[return-value]


# Stufen der Session: judge = Schritt 2 (bank_account), rest = Schritt 3 (QuixBugs), bonus = mit Tests;
# a1 = alles auf einmal (Instructor-Notebook, Vorab-Läufe). judge + rest + bonus = a1.
STAGES = ("judge", "rest", "bonus", "a1")


def stage_variants(model_key: str, stage: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[bool, ...]]:
    """(Snippet-IDs, Haltungen, Testvarianten) einer Stufe. Das lokale Modell bekommt weniger Haltungen
    und keine Läufe mit Tests (Laufzeit auf der T4)."""
    if stage not in STAGES:
        raise ValueError(f"Unbekannte Stufe {stage!r}")
    local = MODELS[model_key]["provider"] == "ollama"
    attitudes = LOCAL_ATTITUDES if local else ATTITUDES
    with_tests = () if local else (True,)
    all_ids = tuple(s.id for s in load_snippets())
    rest = tuple(i for i in all_ids if i != HUMAN_SNIPPET)
    return {
        "judge": ((HUMAN_SNIPPET,), attitudes, (False,)),
        "rest": (rest, attitudes, (False,)),
        "bonus": (all_ids, attitudes, with_tests),
        "a1": (all_ids, attitudes, with_tests + (False,)),
    }[stage]


def assignment1_variants(model_key: str) -> tuple[tuple[str, ...], tuple[bool, ...]]:
    """Haltungen und Testvarianten für Auftrag 1 (alle Stufen zusammen)."""
    _, attitudes, variants = stage_variants(model_key, "a1")
    return attitudes, variants


def run_matrix(
    ctx: RunContext,
    client,
    snippets: Sequence[Snippet],
    attitudes: Sequence[str],
    test_variants: Sequence[bool],
    *,
    on_progress: Progress | None = None,
) -> list[dict]:
    """Auftrag 1: alle Kombinationen Snippet × Haltung × Tests (Reihenfolge wie die Kombinationen)."""
    jobs = [
        (lambda s=s, a=a, t=t: run_one(ctx, client, s, phase="a1", with_tests=t, attitude=a))
        for s in snippets
        for a in attitudes
        for t in test_variants
    ]
    return _run_parallel(jobs, CONCURRENCY.get(client.provider, 1), on_progress)


def run_challenge(
    ctx: RunContext,
    clients: Mapping[str, object],
    prompt_text: str,
    *,
    snippets: Sequence[Snippet],
    submit: bool,
    probe_snippet_id: str | None = None,
    submission_no: int | None = None,
    on_progress: Progress | None = None,
) -> list[dict]:
    """Auftrag 2. Probe: ein Snippet mit dem Gruppenmodell. Einreichung: alle Snippets ohne Tests,
    mit dem Gruppenmodell (a2_submit) und dem Referenzmodell (reference)."""
    group_client = clients["group"]
    if not submit:
        snippet = next((s for s in snippets if s.id == probe_snippet_id), snippets[0])
        record = run_one(ctx, group_client, snippet, phase="a2_probe", with_tests=False, custom_block=prompt_text)
        if on_progress:
            on_progress(1, 1)
        return [record]

    reference_client = clients["reference"]
    submission_id = uuid.uuid4().hex
    total = 2 * len(snippets)
    group_jobs = [
        (lambda s=s: run_one(ctx, group_client, s, phase="a2_submit", with_tests=False,
                             custom_block=prompt_text, submission_no=submission_no, submission_id=submission_id))
        for s in snippets
    ]
    reference_jobs = [
        (lambda s=s: run_one(ctx, reference_client, s, phase="reference", with_tests=False,
                             custom_block=prompt_text, submission_no=submission_no, submission_id=submission_id,
                             model_key="reference"))
        for s in snippets
    ]
    records = _run_parallel(group_jobs, CONCURRENCY.get(group_client.provider, 1), on_progress, 0, total)
    records += _run_parallel(reference_jobs, CONCURRENCY.get(reference_client.provider, 1), on_progress,
                             len(snippets), total)
    return records


def prognosis_record(ctx: RunContext, *, best_model: str, strict_vs_lenient: str) -> dict:
    """Datensatz für die Prognose einer Gruppe (Phase 5–7 min); wird ebenfalls gesendet."""
    record = _empty_record(ctx, "prognosis")
    record.update(
        model_key=ctx.model_key,
        prediction_best_model=best_model,
        prediction_strict_vs_lenient=strict_vs_lenient,
    )
    ctx.sink(record)
    return record
