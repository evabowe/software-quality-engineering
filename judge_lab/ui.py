"""Oberfläche des Hands-on-Notebooks (ipywidgets).

Aufbau: Die Aktionen (``configure``, ``run_assignment1``, ``probe_challenge``,
``submit_challenge``) und Tabellen sind normale Funktionen und getestet; die
Panels verdrahten sie nur mit Widgets. Der Zustand liegt in ``SESSION`` auf
Modulebene, damit er ein erneutes Ausführen einer Zelle übersteht.

Vor der Auflösung zeigt die UI nur, *ob* und *wie viele* Defekte gefunden
wurden, nie *wo* sie liegen.
"""

from __future__ import annotations

import html
import json
import re
import threading
import time
import traceback
from dataclasses import dataclass, field

import ipywidgets as widgets
import pandas as pd
import requests
from IPython.display import HTML, display

from judge_lab import human, join, ollama_colab
from judge_lab.config import (
    CHALLENGE_MAX_SUBMISSIONS,
    DEFAULT_SESSION_ID,
    GROUPS,
    HUMAN_SNIPPET,
    MODELS,
    PROMPTS_DIR,
    SCOREBOARD_TOKEN,
    SCOREBOARD_URL,
)
from judge_lab.llm import ConfigError, MockClient, make_client
from judge_lab.matching import MatchResult
from judge_lab.prompts import lint_challenge_prompt, prompt_hash
from judge_lab.runner import RunContext, prognosis_record, run_challenge, run_matrix, stage_variants
from judge_lab.scoreboard import Scoreboard
from judge_lab.scoring import challenge_points
from judge_lab.snippets import get_snippet, load_snippets

# Klicks, die so kurz nach dem Ende eines Laufs ankommen, gelten als Doppelklick.
DOUBLE_CLICK_S = 1.0

STRICT_VS_LENIENT_OPTIONS = (
    "strict findet mehr Fehler",
    "beide finden etwa gleich viele – strict vergibt nur schlechtere Noten",
    "lenient findet mehr Fehler",
)


@dataclass
class Session:
    group: str | None = None
    model_key: str | None = None
    api_key: str = ""
    mock: bool = False
    session_id: str = DEFAULT_SESSION_ID
    scoreboard: Scoreboard | None = None
    submissions_used: int = 0
    last_submission_hash: str = ""
    local_only: int = 0  # Läufe, die das Scoreboard nicht erreicht haben (nur in der CSV)
    a1_records: list = field(default_factory=list)
    human_record: dict | None = None
    stage_records: dict = field(default_factory=dict)  # Stufe (judge/rest/bonus) → Läufe
    running: set = field(default_factory=set)  # Stufen, die gerade im Hintergrund laufen
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def require_setup(self) -> None:
        if not self.group:
            raise ConfigError("Bitte zuerst Schritt 1 (Setup) ausführen und eure Gruppe wählen.")

    def context(self) -> RunContext:
        self.require_setup()
        return RunContext(group=self.group, model_key=self.model_key, session_id=self.session_id,
                          sink=self._submit)

    def _submit(self, record: dict) -> bool:
        sent = self.scoreboard.submit(record)
        if not sent:
            with self._lock:
                self.local_only += 1
        return sent

    def client(self):
        if self.mock:
            return MockClient()
        if MODELS[self.model_key]["provider"] == "ollama" and not ollama_colab.is_up():
            raise ConfigError(
                "Das lokale Modell läuft noch nicht. Gruppe 4: bitte zuerst die Zelle „🖥️ Nur Gruppe 4“ "
                "ausführen – oder im Setup „ohne GPU“ ankreuzen."
            )
        return make_client(self.model_key, self.api_key)

    def reference_client(self):
        return MockClient() if self.mock else make_client("reference", self.api_key)


SESSION = Session()


def _scoreboard() -> Scoreboard:
    return Scoreboard(SCOREBOARD_URL, SCOREBOARD_TOKEN)


# --- Aktionen -----------------------------------------------------------------


def configure(group: str, api_key: str, *, use_fallback: bool = False, mock: bool = False) -> str:
    """Setzt Gruppe und Modell und prüft Key/Modell-IDs vorab. Wirft ConfigError mit deutscher Meldung."""
    if group not in GROUPS:
        raise ConfigError(f"Unbekannte Gruppe {group!r}.")
    model_key = GROUPS[group]["model_key"]
    if use_fallback and MODELS[model_key]["provider"] == "ollama":
        model_key = "local_fallback"
    if mock:
        model_key = "mock"
    else:
        make_client(model_key, api_key)
        make_client("reference", api_key)
    SESSION.group, SESSION.model_key, SESSION.api_key, SESSION.mock = group, model_key, api_key, mock
    # Mock-Läufe in eine eigene Session, damit sie Leaderboard und Heatmaps nicht verfälschen.
    SESSION.session_id = f"{DEFAULT_SESSION_ID}-mock" if mock else DEFAULT_SESSION_ID
    SESSION.scoreboard = SESSION.scoreboard or _scoreboard()
    return f"✅ Bereit – {group}, euer Judge: {MODELS[model_key]['label']}"


def judge_name(model_key: str) -> str:
    """Kurzname des Judges ohne Klammerzusatz, z. B. „DeepSeek“."""
    return MODELS[model_key]["label"].split(" (")[0]


def join_group(code: str) -> str:
    """Gruppencode → Gruppe und Key vom Code-Server, dann wie ``configure``."""
    group, api_key = join.join(code, url=SCOREBOARD_URL, token=SCOREBOARD_TOKEN, session_id=DEFAULT_SESSION_ID)
    configure(group, api_key)
    return f"✅ Ihr seid {group} – euer Judge heißt {judge_name(SESSION.model_key)}"


def submit_human(lines_text: str, score: int, justification: str, *, correction: bool = False
                 ) -> tuple[dict | None, str]:
    """Schritt 1: Gutachten der Gruppe messen und senden. Einmalig; ``correction`` erlaubt eine Korrektur."""
    SESSION.require_setup()
    if SESSION.human_record and not correction:
        return None, "Ihr habt euer Gutachten schon abgegeben. Korrigieren geht unter „Erweitert“."
    if not justification.strip():
        return None, "Bitte noch eine Begründung in einem Satz eintragen."
    try:
        findings = human.parse_lines(lines_text, get_snippet(HUMAN_SNIPPET).line_count)
    except human.InputError as exc:
        return None, str(exc)
    record = human.human_record(SESSION.context(), findings, score=score, justification=justification.strip())
    SESSION.human_record = record
    return record, human.feedback(record)


def run_assignment1(on_progress=None) -> list[dict]:
    """Alle Stufen auf einmal (wie das frühere Auftrag 1)."""
    return run_stage("a1", on_progress=on_progress)


def run_stage(stage: str, on_progress=None) -> list[dict]:
    """Eine Stufe (judge = Schritt 2, rest = Schritt 3, bonus = mit Tests) mit dem Judge der Gruppe."""
    ids, attitudes, variants = stage_variants(SESSION.model_key, stage)
    snippets = [s for s in load_snippets() if s.id in ids]
    records = run_matrix(SESSION.context(), SESSION.client(), snippets, attitudes, variants, on_progress=on_progress)
    with SESSION._lock:
        SESSION.stage_records[stage] = records
        SESSION.a1_records = [r for stage_runs in SESSION.stage_records.values() for r in stage_runs]
    return records


def start_stage_in_background(stage: str, on_progress=None, on_done=None) -> threading.Thread:
    """Startet eine Stufe in einem Thread, damit die Gruppe weiterarbeiten oder zuhören kann.
    ``on_done(records, None)`` bzw. ``on_done(None, Fehler)`` wird am Ende aufgerufen."""
    SESSION.require_setup()
    with SESSION._lock:
        if stage in SESSION.running:
            raise ConfigError("Diese Beispiele laufen schon – einfach abwarten, der Balken zeigt den Fortschritt.")
        SESSION.running.add(stage)

    def work():
        records, error = None, None
        try:
            records = run_stage(stage, on_progress=on_progress)
        except Exception as exc:  # noqa: BLE001 – wird als Meldung angezeigt
            error = exc
        finally:
            with SESSION._lock:
                SESSION.running.discard(stage)
        if on_done:
            on_done(records, error)

    thread = threading.Thread(target=work, name=f"judge-lab-{stage}", daemon=True)
    thread.start()
    return thread


def probe_challenge(prompt_text: str, snippet_id: str) -> tuple[list[dict] | None, str]:
    if not prompt_text.strip():
        return None, "Der Prompt ist leer."
    records = run_challenge(SESSION.context(), {"group": SESSION.client()}, prompt_text,
                            snippets=load_snippets(), submit=False, probe_snippet_id=snippet_id)
    return records, "Probelauf (zählt nicht)."


def submit_challenge(prompt_text: str, on_progress=None) -> tuple[list[dict] | None, str]:
    if not prompt_text.strip():
        return None, "Der Prompt ist leer."
    if SESSION.submissions_used >= CHALLENGE_MAX_SUBMISSIONS:
        return None, f"Ihr habt keine Einreichung mehr übrig ({CHALLENGE_MAX_SUBMISSIONS} von {CHALLENGE_MAX_SUBMISSIONS})."
    if prompt_hash(prompt_text) == SESSION.last_submission_hash:
        return None, "Diesen Prompt habt ihr schon eingereicht – ändert ihn vor der nächsten Einreichung."
    SESSION.require_setup()
    # Vor dem Lauf hochzählen, damit ein abgebrochener Lauf nicht wiederholt eingereicht werden kann.
    SESSION.submissions_used += 1
    SESSION.last_submission_hash = prompt_hash(prompt_text)
    number = SESSION.submissions_used
    clients = {"group": SESSION.client(), "reference": SESSION.reference_client()}
    records = run_challenge(SESSION.context(), clients, prompt_text, snippets=load_snippets(), submit=True,
                            submission_no=number, on_progress=on_progress)
    return records, f"Einreichung {number}/{CHALLENGE_MAX_SUBMISSIONS} ausgewertet."


# --- Tabellen -------------------------------------------------------------------


def _titles() -> dict[str, str]:
    return {s.id: s.title for s in load_snippets()}


def _failed(record: dict) -> bool:
    """Lauf ohne Urteil wegen Infrastruktur (Key, Limit, Netz) – nicht wegen des Judges."""
    return record["parse_ok"] is None


def error_summary(records: list[dict]) -> list[str]:
    """Verschiedene Fehlermeldungen der fehlgeschlagenen Läufe mit Anzahl."""
    counts: dict[str, int] = {}
    for r in records:
        if _failed(r):
            counts[r["error"]] = counts.get(r["error"], 0) + 1
    return [f"{n}× {message}" for message, n in counts.items()]


def _cell(record: dict) -> str:
    if _failed(record):
        return "Fehler"
    found = f"{record['tp']}/{record['n_defects']}"
    if not record["parse_ok"]:
        return f"unlesbar · {found}"
    score = record["weighted_score"]
    return f"{score:.1f} · {found}" if score is not None else f"– · {found}"


def assignment1_table(records: list[dict]) -> pd.DataFrame:
    """Zeilen = Snippets, Spalten = Haltung × Tests, Zellen = „Score · gefunden x/y“."""
    titles = _titles()
    rows = {}
    for r in records:
        column = f"{r['attitude']} · {'mit' if r['with_tests'] else 'ohne'} Tests"
        rows.setdefault(titles[r["snippet_id"]], {})[column] = _cell(r)
    table = pd.DataFrame.from_dict(rows, orient="index")
    order = [t for t in titles.values() if t in table.index]
    return table.loc[order].fillna("")


def findings_table(records: list[dict]) -> pd.DataFrame:
    """Die Befunde des Judges im Wortlaut (ohne Abgleich mit der Ground Truth)."""
    titles = _titles()
    rows = []
    for r in records:
        try:
            findings = json.loads(r["findings_json"]) if r["findings_json"] else []
        except json.JSONDecodeError:  # gekürzt
            findings = []
        for f in findings:
            rows.append({
                "Snippet": titles[r["snippet_id"]],
                "Haltung": r["attitude"],
                "Tests": "mit" if r["with_tests"] else "ohne",
                "Zeilen (laut Judge)": f"{f['line_start']}–{f['line_end']}",
                "Kategorie": f["category"],
                "Beschreibung": f["description"],
            })
    return pd.DataFrame(rows)


def _result(record: dict) -> MatchResult:
    # Fehlgeschlagene Läufe (tp/fp leer) zählen 0 Punkte.
    return MatchResult(tp=record["tp"] or 0, fp=record["fp"] or 0, neutral=record["neutral"] or 0,
                       n_defects=record["n_defects"], found_defect_ids=(), assignments={}, recall=None, precision=None)


def challenge_summary(records: list[dict]) -> pd.DataFrame:
    """Treffer ✔/✘ je Snippet, Fehlalarme und Punkte für Gruppenmodell und Referenzmodell."""
    titles = _titles()
    own = [r for r in records if r["phase"] == "a2_submit"]
    reference = {r["snippet_id"]: r for r in records if r["phase"] == "reference"}
    rows = {}
    for r in own:
        mark = "✔" if r["tp"] else "✘"
        ref = reference.get(r["snippet_id"])
        rows[titles[r["snippet_id"]]] = {
            "Treffer": "Fehler" if _failed(r) else f"{mark} {r['tp']}/{r['n_defects']}",
            "Fehlalarme": r["fp"],
            "Punkte": challenge_points([_result(r)]),
            "Punkte Referenz": challenge_points([_result(ref)]) if ref else None,
        }
    table = pd.DataFrame.from_dict(rows, orient="index", columns=["Treffer", "Fehlalarme", "Punkte", "Punkte Referenz"])
    table.loc["Summe"] = [
        "",
        sum(r["fp"] or 0 for r in own),
        challenge_points(_result(r) for r in own),
        challenge_points(_result(r) for r in reference.values()) if reference else None,
    ]
    return table


REASON_CHARS = 200
ROLE_LABELS = {"strict": "strict", "objective": "objective", "lenient": "lenient", "none": "keine Rolle"}


def _reason(record: dict) -> str:
    """Erste 200 Zeichen der Befunde des LLM (Wortlaut, ohne Abgleich mit der Ground Truth)."""
    try:
        findings = json.loads(record["findings_json"]) if record["findings_json"] else []
    except json.JSONDecodeError:
        findings = []
    text = "; ".join(f.get("description", "") for f in findings if f.get("description"))
    return text if len(text) <= REASON_CHARS else text[:REASON_CHARS] + "…"


def comparison_table(human_record: dict | None, judge_records: list[dict]) -> pd.DataFrame:
    """Schritt 2: euer Gutachten neben dem LLM in den drei Haltungen (gleicher Code)."""
    rows = {}
    if human_record:
        label = f"Ihr ({ROLE_LABELS.get(human_record['attitude'], human_record['attitude'])})"
        rows[label] = {"Score": f"{human_record['weighted_score']}",
                       "gefunden": f"{human_record['tp']}/{human_record['n_defects']}",
                       "Fehlalarme": human_record["fp"], "Begründung": human.justification_of(human_record)}
    else:
        rows["Ihr"] = {"Score": "–", "gefunden": "–", "Fehlalarme": "–", "Begründung": "noch kein Gutachten"}
    order = {a: i for i, a in enumerate(("strict", "objective", "lenient"))}
    for r in sorted(judge_records, key=lambda r: order.get(r["attitude"], 9)):
        if _failed(r):
            rows[f"LLM {r['attitude']}"] = {"Score": "Fehler", "gefunden": "–", "Fehlalarme": "–", "Begründung": r["error"]}
            continue
        score = r["weighted_score"]
        rows[f"LLM {r['attitude']}"] = {
            "Score": f"{score:.1f}" if score is not None else "–",
            "gefunden": f"{r['tp']}/{r['n_defects']}" + ("" if r["parse_ok"] else " (unlesbar)"),
            "Fehlalarme": r["fp"],
            "Begründung": _reason(r),
        }
    return pd.DataFrame.from_dict(rows, orient="index", columns=["Score", "gefunden", "Fehlalarme", "Begründung"])


def snippet_html(snippet_id: str) -> str:
    """Snippet mit Zeilennummern, ohne Ground Truth."""
    snippet = get_snippet(snippet_id)
    view = snippet.public_view()
    level = view["level"] or "ohne Stufe"
    return (
        f"<h4>{html.escape(view['title'])} <small>({html.escape(view['id'])}, {level})</small></h4>"
        f"<pre style='font-size:13px;line-height:1.35'>{html.escape(snippet.numbered_code())}</pre>"
    )


def local_only_warning(before: int) -> str | None:
    """Hinweis, wenn seit ``before`` Läufe nur lokal gesichert wurden."""
    missing = SESSION.local_only - before
    if missing <= 0:
        return None
    return (f"⚠️ {missing} Läufe haben das Scoreboard nicht erreicht und sind nur lokal gesichert "
            f"({SESSION.scoreboard.backup_path.name}). Bitte Bescheid geben – sie werden später nachgesendet.")


def _show_local_only(before: int) -> None:
    warning = local_only_warning(before)
    if warning:
        display(HTML(f"<div style='color:#b45309'><b>{html.escape(warning)}</b></div>"))


def friendly_error(exc: BaseException) -> str:
    if isinstance(exc, (ConfigError, human.InputError)):
        return f"⚠️ {exc}"
    if isinstance(exc, requests.RequestException):
        return "⚠️ Keine Verbindung zum Server. Bitte WLAN prüfen und erneut versuchen."
    return f"⚠️ Unerwarteter Fehler ({type(exc).__name__}: {exc}). Bitte Bescheid geben."


# --- Widgets --------------------------------------------------------------------


def _show_error(out: widgets.Output, exc: BaseException) -> None:
    details = widgets.Output()
    with details:
        print(traceback.format_exc())
    debug = widgets.Accordion(children=[details])
    debug.set_title(0, "Details für die Betreuung")
    debug.selected_index = None
    with out:
        display(HTML(f"<b>{html.escape(friendly_error(exc))}</b>"), debug)


def _show_failures(records: list[dict]) -> None:
    lines = error_summary(records)
    if lines:
        items = "".join(f"<li>{html.escape(line)}</li>" for line in lines)
        display(HTML(f"<div style='color:#b45309'><b>⚠️ Einige Läufe sind fehlgeschlagen "
                     f"(zählen nicht als Ergebnis des Judges):</b><ul>{items}</ul></div>"))


def _debounced(action, now=time.monotonic):
    """Ignoriert Klicks während eines Laufs und kurz danach.

    ipywidgets arbeitet Klicks nacheinander ab; ein Doppelklick startet den zweiten Lauf also
    erst, wenn der erste fertig ist (und der Button wieder aktiv). Genau diesen Klick verwerfen wir.
    """
    state = {"busy": False, "finished": float("-inf")}

    def handler(*args):
        if state["busy"] or now() - state["finished"] < DOUBLE_CLICK_S:
            return
        state["busy"] = True
        try:
            action(*args)
        finally:
            state["busy"] = False
            state["finished"] = now()

    return handler


def _guarded(out: widgets.Output, action):
    """Fehler in Button-Handlern als deutsche Meldung statt Traceback anzeigen."""

    def handler(*args):
        try:
            action(*args)
        except Exception as exc:  # noqa: BLE001
            _show_error(out, exc)

    return handler


def _initial_api_key() -> str:
    try:
        from google.colab import userdata  # nur in Colab verfügbar

        return userdata.get("OPENROUTER_API_KEY") or ""
    except Exception:  # noqa: BLE001 – kein Colab oder Secret nicht freigegeben
        return ""


def setup_panel(on_saved=None) -> widgets.Widget:
    group = widgets.Dropdown(options=list(GROUPS), value=SESSION.group, description="Gruppe:")
    model = widgets.HTML()
    key = widgets.Password(value=SESSION.api_key or _initial_api_key(), description="API-Key:",
                           placeholder="sk-or-… (siehe Folie)")
    fallback = widgets.Checkbox(value=False, description="Gruppe 4 ohne GPU: kleines Modell über OpenRouter")
    mock = widgets.Checkbox(value=SESSION.mock, description="Probemodus (Mock, keine Kosten)")
    button = widgets.Button(description="Speichern", button_style="primary")
    out = widgets.Output()

    def show_model(*_):
        if group.value:
            model.value = f"Euer Judge: <b>{html.escape(MODELS[GROUPS[group.value]['model_key']]['label'])}</b>"

    def save(*_):
        out.clear_output()
        message = configure(group.value, key.value.strip(), use_fallback=fallback.value, mock=mock.value)
        with out:
            display(HTML(f"<b>{html.escape(message)}</b>"))
        if on_saved:
            on_saved()

    group.observe(show_model, names="value")
    show_model()
    button.on_click(_guarded(out, save))
    return widgets.VBox([group, model, key, fallback, mock, button, out])


def role_card_html(group: str | None) -> str:
    if not group:
        return "<p>Bitte zuerst im Reiter „Start“ den Gruppencode eingeben – dann erscheint hier eure Rollenkarte.</p>"
    card = html.escape(human.role_card(group))
    card = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", card).replace("\n", "<br>")
    return (
        "<div style='background:#fff7e6;border:2px solid #f0b429;border-radius:6px;padding:10px 14px;max-width:60em'>"
        f"<div style='font-size:1.1em'><b>🤫 Eure Rollenkarte – Nicht verraten!</b></div><p>{card}</p></div>"
    )


HUMAN_INSTRUCTIONS = """
<p>Lest den Code und bewertet ihn <b>in eurer Rolle</b>:</p>
<ol>
  <li><b>Zeilen mit Fehlern</b> – einzelne Zeilen oder Bereiche, z. B. <code>26, 31, 39-40</code> (oder „keine“)</li>
  <li><b>Score 1–10</b> – wie gut ist der Code insgesamt?</li>
  <li><b>Begründung</b> in einem Satz</li>
</ol>
<p>Abgeben könnt ihr einmal. Danach seht ihr, <i>wie viele</i> Defekte ihr gefunden habt – <i>welche</i>, verraten wir erst bei der Auflösung.</p>
"""


@dataclass
class HumanPanel:
    widget: widgets.Widget
    card: widgets.HTML
    lines: widgets.Text
    score: widgets.IntSlider
    justification: widgets.Text
    submit: widgets.Button
    message: widgets.HTML

    def refresh(self) -> None:
        self.card.value = role_card_html(SESSION.group)


def human_panel() -> HumanPanel:
    card = widgets.HTML(role_card_html(SESSION.group))
    wide = {"description_width": "initial"}
    lines = widgets.Text(placeholder="z. B. 26, 31, 39-40", description="Zeilen mit Fehlern:", style=wide,
                         layout=widgets.Layout(width="30em"))
    score = widgets.IntSlider(value=5, min=1, max=10, description="Score 1–10:", style=wide)
    justification = widgets.Text(placeholder="ein Satz", description="Begründung:", style=wide,
                                 layout=widgets.Layout(width="60em"))
    submit = widgets.Button(description="Gutachten abgeben", button_style="primary")
    message = widgets.HTML()
    correct = widgets.Button(description="Gutachten korrigieren")
    advanced = widgets.Accordion(children=[widgets.VBox([
        widgets.HTML("Nur nach Rücksprache: Die korrigierte Fassung ersetzt die erste auf dem Scoreboard."), correct])])
    advanced.set_title(0, "Erweitert")
    advanced.selected_index = None
    panel = HumanPanel(widgets.VBox([card, widgets.HTML(HUMAN_INSTRUCTIONS), widgets.HTML(snippet_html(HUMAN_SNIPPET)),
                                     lines, score, justification, submit, message, advanced]),
                       card, lines, score, justification, submit, message)
    state = {"correction": False}

    def lock():
        submit.disabled, submit.description = True, "✅ abgegeben"

    def send(*_):
        card.value = role_card_html(SESSION.group)
        record, text = submit_human(lines.value, score.value, justification.value, correction=state["correction"])
        color = "#1f2933" if record else "#b45309"
        message.value = f"<div style='color:{color};font-size:1.1em'><b>{html.escape(text)}</b></div>"
        if record:
            state["correction"] = False
            lock()

    def unlock(*_):
        state["correction"] = True
        submit.disabled, submit.description = False, "Korrektur abgeben"

    if SESSION.human_record:
        lock()
        message.value = f"<b>{html.escape(human.feedback(SESSION.human_record))}</b>"
    submit.on_click(_guarded_html(message, _debounced(send)))
    correct.on_click(unlock)
    return panel


def _guarded_html(target: widgets.HTML, action):
    """Wie ``_guarded``, aber die Meldung landet in einem HTML-Widget (funktioniert auch aus Threads)."""

    def handler(*args):
        try:
            action(*args)
        except Exception as exc:  # noqa: BLE001
            target.value = f"<div style='color:#b45309'><b>{html.escape(friendly_error(exc))}</b></div>"

    return handler


def best_judge_options() -> list[tuple[str, str]]:
    return [(MODELS[g["model_key"]]["label"], g["model_key"]) for g in GROUPS.values()] + [("wir Menschen", "human")]


def _warning(text: str) -> str:
    return f"<div style='color:#b45309'><b>{html.escape(text)}</b></div>"


def _failures_html(records: list[dict]) -> str:
    lines = error_summary(records)
    if not lines:
        return ""
    items = "".join(f"<li>{html.escape(line)}</li>" for line in lines)
    return (f"<div style='color:#b45309'><b>⚠️ Einige Läufe sind fehlgeschlagen "
            f"(zählen nicht als Ergebnis des Judges):</b><ul>{items}</ul></div>")


def _local_only_html(before: int) -> str:
    warning = local_only_warning(before)
    return _warning(warning) if warning else ""


def prognosis_panel() -> widgets.Widget:
    wide = {"description_width": "initial"}
    strict = widgets.Dropdown(options=STRICT_VS_LENIENT_OPTIONS, description="H1:", style=wide,
                              layout=widgets.Layout(width="45em"))
    best = widgets.Dropdown(options=best_judge_options(), description="H2:", style=wide)
    button = widgets.Button(description="Prognose absenden", button_style="primary")
    message = widgets.HTML()

    def send(*_):
        before = SESSION.local_only
        prognosis_record(SESSION.context(), best_model=best.value, strict_vs_lenient=strict.value)
        message.value = "<b>✅ Prognose gespeichert.</b>" + _local_only_html(before)

    button.on_click(_guarded_html(message, _debounced(send)))
    return widgets.VBox([
        widgets.HTML("<h4>Eure Prognose</h4><p><b>H1:</b> Findet <i>strict</i> mehr echte Fehler als "
                     "<i>lenient</i> – oder vergibt es nur schlechtere Noten?</p>"),
        strict,
        widgets.HTML("<p><b>H2:</b> Welcher Judge findet die meisten Defekte?</p>"),
        best, button, message,
    ])


@dataclass
class StagePanel:
    widget: widgets.Widget
    run: widgets.Button
    progress: widgets.IntProgress
    result: widgets.HTML


def _progress_bar() -> tuple[widgets.IntProgress, callable]:
    progress = widgets.IntProgress(value=0, min=0, max=1, description="0/0")

    def update(done, total):
        progress.max, progress.value, progress.description = total, done, f"{done}/{total}"

    return progress, update


def llm_judge_panel() -> StagePanel:
    """Schritt 2: derselbe Code, das LLM als Judge in drei Haltungen; Vergleich mit eurem Gutachten."""
    run = widgets.Button(description="Unseren Judge bewerten lassen", button_style="primary",
                         layout=widgets.Layout(width="auto"))
    progress, update = _progress_bar()
    result = widgets.HTML()

    def start(*_):
        run.disabled = True
        before = SESSION.local_only
        records = []
        try:
            records = run_stage("judge", on_progress=update)
        finally:
            # Bei Infrastrukturfehlern darf die Gruppe es noch einmal versuchen.
            ok = records and not error_summary(records)
            run.disabled = bool(ok)
            run.description = "✅ erledigt" if ok else "Unseren Judge bewerten lassen"
        table = comparison_table(SESSION.human_record, records)
        result.value = (_local_only_html(before) + _failures_html(records)
                        + "<h4>Mensch vs. LLM – gleicher Code (bank_account)</h4>" + table.to_html(escape=True))

    run.on_click(_guarded_html(result, _debounced(start)))
    return StagePanel(widgets.VBox([prognosis_panel(), widgets.HTML("<hr>"), run, progress, result]),
                      run, progress, result)


def _a1_result_html() -> str:
    records = SESSION.a1_records
    if not records:
        return ""
    findings = findings_table(records)
    return (_failures_html(records) + "<h4>Score · gefundene Defekte (je Beispiel und Bedingung)</h4>"
            + assignment1_table(records).to_html(escape=True)
            + "<details><summary>Was die Judges gemeldet haben (Wortlaut)</summary>"
            + findings.to_html(escape=True, index=False) + "</details>")


def all_examples_panel() -> StagePanel:
    """Schritt 3: die übrigen Beispiele im Hintergrund; Bonus mit Tests als Kontext (nur API-Modelle)."""
    run = widgets.Button(description="Restliche Beispiele starten", button_style="primary",
                         layout=widgets.Layout(width="auto"))
    bonus = widgets.Button(description="Bonus: mit Tests als Kontext", layout=widgets.Layout(width="auto"))
    progress, update = _progress_bar()
    status = widgets.HTML()
    result = widgets.HTML(_a1_result_html())

    def launch(stage, button, label):
        def on_done(records, error):
            before = SESSION.local_only
            if error is not None:
                status.value = _warning(friendly_error(error))
                button.disabled, button.description = False, label
                return
            ok = not error_summary(records)
            button.disabled, button.description = ok, ("✅ erledigt" if ok else label)
            status.value = _local_only_html(before)
            result.value = _a1_result_html()

        def start(*_):
            button.disabled, button.description = True, "läuft im Hintergrund …"
            status.value = "<i>Läuft im Hintergrund – ihr könnt den Reiter wechseln oder zuhören.</i>"
            start_stage_in_background(stage, on_progress=update, on_done=on_done)

        return _guarded_html(status, _debounced(start))

    run.on_click(launch("rest", run, run.description))
    bonus.on_click(launch("bonus", bonus, bonus.description))
    has_bonus = any(stage_variants(SESSION.model_key, "bonus")[2]) if SESSION.model_key else True
    buttons = [run, bonus] if has_bonus else [run]
    return StagePanel(widgets.VBox([widgets.HBox(buttons), progress, status, result]), run, progress, result)


def snippet_viewer() -> widgets.Widget:
    options = [(f"{s.title} ({s.level or 'ohne Stufe'})", s.id) for s in load_snippets()]
    choice = widgets.Dropdown(options=options, description="Snippet:")
    out = widgets.Output()

    def show(*_):
        out.clear_output()
        with out:
            display(HTML(snippet_html(choice.value)))

    choice.observe(show, names="value")
    show()
    return widgets.VBox([choice, out])


def assignment1_panel() -> widgets.Widget:
    button = widgets.Button(description="Auftrag 1 starten", button_style="primary")
    progress = widgets.IntProgress(value=0, min=0, max=1, description="0/0")
    out = widgets.Output()

    def update(done, total):
        progress.max, progress.value, progress.description = total, done, f"{done}/{total}"

    def start(*_):
        out.clear_output()
        button.disabled = True
        before = SESSION.local_only
        try:
            records = run_assignment1(on_progress=update)
        finally:
            button.disabled = False
        with out:
            _show_local_only(before)
            _show_failures(records)
            display(HTML("<b>Score · gefundene Defekte</b> (je Snippet und Bedingung)"),
                    assignment1_table(records))
            findings = widgets.Output()
            with findings:
                display(findings_table(records))
            details = widgets.Accordion(children=[findings])
            details.set_title(0, "Was die Judges gemeldet haben (Wortlaut)")
            details.selected_index = None
            display(details)

    button.on_click(_guarded(out, _debounced(start)))
    return widgets.VBox([button, progress, out])


def _submit_label() -> str:
    next_number = min(SESSION.submissions_used + 1, CHALLENGE_MAX_SUBMISSIONS)
    return f"Einreichen ({next_number}/{CHALLENGE_MAX_SUBMISSIONS})"


def assignment2_panel() -> widgets.Widget:
    baseline = (PROMPTS_DIR / "challenge_baseline.md").read_text(encoding="utf-8")
    text = widgets.Textarea(value=baseline, layout=widgets.Layout(width="100%", height="22em"))
    lint = widgets.HTML()
    probe_choice = widgets.Dropdown(options=[(s.title, s.id) for s in load_snippets()], description="Probe auf:")
    probe = widgets.Button(description="Probelauf")
    submit = widgets.Button(description=_submit_label(), button_style="warning",
                            disabled=SESSION.submissions_used >= CHALLENGE_MAX_SUBMISSIONS)
    progress = widgets.IntProgress(value=0, min=0, max=1)
    out = widgets.Output()

    def check(*_):
        warnings = lint_challenge_prompt(text.value, load_snippets())
        lint.value = "".join(f"<div style='color:#b45309'>⚠️ {html.escape(w)}</div>" for w in warnings)

    def update(done, total):
        progress.max, progress.value = total, done

    def run_probe(*_):
        out.clear_output()
        records, message = probe_challenge(text.value, probe_choice.value)
        with out:
            print(message)
            if records:
                r = records[0]
                print(f"Gefunden: {r['tp']}/{r['n_defects']} · Fehlalarme: {r['fp']} · lesbar: {r['parse_ok']}")
                display(findings_table(records))

    def run_submit(*_):
        out.clear_output()
        submit.disabled = True
        before = SESSION.local_only
        try:
            records, message = submit_challenge(text.value, on_progress=update)
        finally:
            submit.description = _submit_label()
            submit.disabled = SESSION.submissions_used >= CHALLENGE_MAX_SUBMISSIONS
        with out:
            print(message)
            _show_local_only(before)
            if records:
                _show_failures(records)
                display(challenge_summary(records))

    text.observe(check, names="value")
    check()
    probe.on_click(_guarded(out, _debounced(run_probe)))
    submit.on_click(_guarded(out, _debounced(run_submit)))
    return widgets.VBox([text, lint, widgets.HBox([probe_choice, probe]), submit, progress, out])
