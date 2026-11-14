# Vier Bausteine für Jessicas Notebook – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das Paket `judge_lab` auf genau vier öffentliche Funktionen reduzieren (`verbinde`, `bewerte`, `bewerte_alle`, `sende`) und ein schlankes Kachel-Dashboard bauen, das deren Daten live zeigt.

**Architecture:** Das vorhandene Paket wird ausgedünnt. Erhalten bleiben Join, Prompt-Aufbau, JSON-Reparatur, Parsing, Ground-Truth-Abgleich und CSV-Sicherung. Darauf setzt ein neues Modul `judge_lab/bausteine.py` mit Modulzustand (Gruppe, Key). `scoreboard/Code.gs` nimmt Zeilen an und aggregiert sie zu Kacheln je Runde, `dashboard.html` rendert sie.

**Tech Stack:** Python ≥ 3.10 (openai-SDK, pydantic, requests, pyyaml), pytest, Google Apps Script (V8), Node ≥ 18 für `node --test`, Chart.js 4 im Dashboard.

**Spec:** `docs/superpowers/specs/2026-11-14-bausteine-design.md`

## Global Constraints

- Genau vier öffentliche Funktionen: `from judge_lab import verbinde, bewerte, bewerte_alle, sende`. Keine fünfte öffentliche Funktion, keine Widgets.
- Nur OpenRouter (`https://openrouter.ai/api/v1`). Standardmodell `DEFAULT_MODEL = "openai/gpt-6-luna"`. `modell="mock"` nutzt den Mock-Client (für Tests, braucht kein `verbinde`).
- `code_score` = `scoring.weighted_score(verdict.scores)` (0–10, `None` bei fehlender Dimension). `judge_score` = `2·tp − 1·fp` aus `match_findings` (`config.POINTS = {"tp": 2, "fp_bug": -1}`).
- Snippet-Tests nie im Prompt (`with_tests=False`). `temperature=0`, JSON-Modus, ein Reparatur-Versuch.
- Runden: 1 = Frei ausprobieren, 2 = Rollen vergleichen, 3 = Komplexität vergleichen, 4 = AI Challenge. Runden 1–2: einzelnes Ergebnis. Runden 3–4: Liste aus `bewerte_alle`.
- `bewerte_alle` = die fünf Snippets mit Stufe, L1 `qb_bitcount`, L2 `qb_quicksort`, L3 `qb_levenshtein`, L4 `qb_shunting_yard`, L5 `qb_next_permutation`, parallel mit 6 Workern. Kein `bank_account`.
- Kein Traceback für Studierende: Alle vier Funktionen fangen erwartbare Fehler ab und geben kurze deutsche Meldungen mit `print` aus.
- Fehlgeschlagene Läufe (`fehler` gesetzt) und Mock-Ergebnisse werden nie gesendet.
- `session_id` setzt Apps Script beim Empfang aus dem Tab `config`. Python kennt keine Sessions.
- **Notebooks nicht anfassen:** Nichts in `notebooks/` ändern oder löschen (Ausnahme: das neue, nicht committete `notebooks/eva_test.ipynb`). `tools/build_notebooks.py` bleibt.
- Arbeit direkt auf `feature/interactive-session`. Commit-Nachrichten auf Deutsch im Stil `feat: …` / `chore: …` / `docs: …`, **ohne** `Co-Authored-By`-Zeile (Evas Vorgabe).
- Alle Texte für Nutzerinnen auf Deutsch, kurz, ohne Fachjargon.

## Review Focus

1. **Zelle doppelt ausgeführt:** Dasselbe Ergebnis wird zweimal gesendet. Das Dashboard zählt es einmal, weil es nach `run_id` dedupliziert (Node-Test in Task 5).
2. **Sheet während `sende` einer Fünferliste nicht erreichbar:** Alle fünf Zeilen landen in der CSV. Der nächste erfolgreiche `sende` schickt sie zuerst nach (Test in Task 4).
3. **LLM liefert Findings, aber keine vollständigen Scores:** `code_score=None`, `judge_score` ist trotzdem gesetzt, `fehler=None`. Die Zeile wird gesendet, die Kachel zeigt „–“, und der Runde-4-Durchschnitt ignoriert den Wert (Tests in Task 3 und 5).
4. **Notfall-`verbinde(key=…, gruppe="Team Rot")` mit einer Gruppe, die nicht im Tab `keys` steht:** Die Gruppe bekommt trotzdem eine Kachel, angehängt nach den Gruppen aus `keys` (Node-Test in Task 5).
5. **Prompt beginnt mit `-`, `=` oder `+`** (Markdown-Liste): Er wird im Sheet als Text gespeichert, nicht als Formel (bestehender `cellValue`-Test bleibt in Task 5).

---

## File Structure

| Datei | Verantwortung |
|---|---|
| `judge_lab/__init__.py` | exportiert genau die vier Funktionen |
| `judge_lab/bausteine.py` (neu) | Modulzustand + die vier Funktionen |
| `judge_lab/config.py` | Pfade, `DEFAULT_MODEL`, Gewichte, Punkte, Timeouts, Scoreboard-URL/Token |
| `judge_lab/llm.py` | `ChatClient`, `MockClient`, `make_client(modell, api_key)` |
| `judge_lab/runner.py` | nur noch `judge()` (Aufruf + Reparatur-Versuch) |
| `judge_lab/join.py` | Code → (Gruppe, Key) |
| `judge_lab/scoreboard.py` | `RECORD_FIELDS`, `Scoreboard.submit(records)`, CSV-Sicherung |
| `judge_lab/{parsing,matching,scoring,prompts,snippets}.py` | unverändert bis auf das Entfernen von `lint_challenge_prompt` |
| `scoreboard/Code.gs` | Empfang, Join, Aggregation zu Kacheln |
| `scoreboard/dashboard.html` | Reiter 1–4, 2×2-Kacheln, Diagramm in Runde 3 |
| `scoreboard/aggregate.test.mjs` | Node-Tests der Aggregation |
| `tools/dashboard_preview.mjs` | statische Vorschau mit Beispieldaten |
| `docs/BAUSTEINE.md`, `docs/DASHBOARD_TEST.md`, `README.md` | die einzige Doku |

---

### Task 1: Abgelehntes Setup entfernen, Kern verschlanken

**Files:**
- Delete: `judge_lab/{ui,app,human,phase,instructor,ollama_colab}.py`, `tests/test_{ui,app,human,phase,instructor,ollama_colab,notebooks}.py`, `prompts/role_cards_de.md`
- Modify: `judge_lab/config.py`, `judge_lab/llm.py`, `judge_lab/runner.py`, `judge_lab/prompts.py`, `judge_lab/join.py`, `judge_lab/__init__.py`, `pyproject.toml`
- Test: `tests/test_llm.py`, `tests/test_runner.py`, `tests/test_prompts.py`, `tests/test_join.py`, `tests/test_scoreboard_contract.py`

**Interfaces:**
- Produces:
  - `config.DEFAULT_MODEL = "openai/gpt-6-luna"`, `config.OPENROUTER_BASE_URL`, `config.TIMEOUT_S = 90`, `config.CONCURRENCY = 6`, `config.MAX_RETRIES`, `config.TEMPERATURE`, `config.MAX_TOKENS`, `config.WEIGHTS`, `config.POINTS`, `config.ATTITUDES`, `config.SCOREBOARD_URL`, `config.SCOREBOARD_TOKEN`, `config.SCOREBOARD_TIMEOUT`, `config.SCOREBOARD_RETRIES`, `config.SNIPPETS_DIR`, `config.PROMPTS_DIR`.
  - `llm.make_client(modell: str, api_key: str | None) -> ChatClient | MockClient`. `"mock"` liefert `MockClient()`. Sonst `ChatClient` gegen OpenRouter. Ein leerer Key wirft `ConfigError("Es fehlt der OpenRouter-Key. Bitte zuerst verbinde(\"CODE\") mit dem Code von der Folie ausführen.")`.
  - `runner.judge(client, messages, line_count) -> tuple[JudgeVerdict | None, LLMResult, bool]` (unverändert).
  - `join.join(code: str, *, url: str, token: str, get=requests.get) -> tuple[str, str]`. Kein `session_id`-Parameter mehr, keine Prüfung gegen `GROUPS`.

- [ ] **Step 1: Module, Tests und Rollenkarten löschen** (Liste oben). `git rm` verwenden. `notebooks/` und `tools/build_notebooks.py` bleiben unberührt.
- [ ] **Step 2: Tests an den neuen Kern anpassen.**
  - `tests/test_llm.py`: `test_make_client_placeholder_id`, `test_make_client_unknown_model` und `test_make_client_ollama_needs_no_key` löschen, `test_mock_scores_depend_on_attitude` behalten. Neu:
    ```python
    def test_make_client_any_openrouter_id():
        client = make_client("openai/gpt-6-luna", "sk-test")
        assert client.provider == "openrouter" and client.model_id == "openai/gpt-6-luna"

    def test_make_client_mock_needs_no_key():
        assert make_client("mock", None).model_id == "mock"

    def test_make_client_missing_key():
        with pytest.raises(ConfigError, match="verbinde"):
            make_client("openai/gpt-6-luna", "")
    ```
  - `tests/test_runner.py`: nur `test_repair_retry_used_once`, `test_repair_fails_gives_parse_ok_false` (umbenannt in `test_repair_fails_gives_none`) und `test_llm_error_is_not_counted_as_judge_result` behalten, alle auf `judge()` umgeschrieben. Alles zu Matrix, Stages, Challenge, Prognose und Records löschen.
  - `tests/test_prompts.py`: die drei `test_lint_*` löschen.
  - `tests/test_join.py`: `ui`-Import, `test_unknown_group_from_server_is_rejected` und `test_join_group_configures_session` löschen. Die Aufrufe ohne `session_id`. Neu: `test_join_accepts_any_group_name` (Server antwortet `group: "Team Rot"` → `("Team Rot", key)`).
  - `tests/test_scoreboard_contract.py`: `test_strict_vs_lenient_options_match`, `test_groups_match` und `test_points_match` löschen.
- [ ] **Step 3: Tests laufen lassen und Fehler sehen.** `python -m pytest -q`. Erwartet: FAIL in `test_llm`/`test_join` (alte Signaturen).
- [ ] **Step 4: Kern anpassen.**
  - `config.py`: Entfernen `MODELS`, `PLACEHOLDER_MARK`, `GROUPS`, `OLLAMA_BASE_URL`, `LOCAL_ATTITUDES`, `HUMAN_*`, `CHALLENGE_MAX_SUBMISSIONS`, `DEFAULT_SESSION_ID`, `FINDINGS_JSON_MAX`, `TIMEOUTS`. `CONCURRENCY` wird eine Zahl.
  - `llm.py`: `make_client` wie oben.
  - `runner.py`: alles außer `_combine` und `judge` löschen.
  - `prompts.py`: `lint_challenge_prompt` und `_LINE_REFERENCE` löschen.
  - `join.py`: wie oben.
  - `__init__.py`: `NOTEBOOK_VERSION` entfernen. Die Exporte kommen in Task 3.
  - `pyproject.toml`: `ipywidgets` raus. `pandas` und `complexipy` bleiben (`notebooks/complexity.ipynb`, `tools/compute_complexity.py`).
- [ ] **Step 5: Tests grün.** `python -m pytest -q`. Erwartet: alles PASS. Der Node-Test der alten Aggregation läuft weiter grün, weil `Code.gs` noch unverändert ist.
- [ ] **Step 6: Prüfen, dass nichts mehr entfernte Module importiert.** `grep -rnE "judge_lab\.(ui|app|human|phase|instructor|ollama_colab)|from judge_lab import (ui|app)" judge_lab tests tools`. Erwartet: keine Treffer (Notebooks ausgenommen).
- [ ] **Step 7: Commit** `chore: Oberfläche, Phasen, Rollenkarten und lokale Modelle entfernen`

### Task 2: Neuer Datenvertrag und Scoreboard für Listen

**Files:**
- Modify: `judge_lab/scoreboard.py`
- Test: `tests/test_scoreboard.py`

**Interfaces:**
- Produces:
  - `RECORD_FIELDS = ("timestamp", "run_id", "gruppe", "runde", "snippet", "komplexitaet", "modell", "prompt", "code_score", "judge_score", "einreichung")`. `session_id` fehlt bewusst, Apps Script setzt es.
  - `Scoreboard(url, token, backup_path=None, *, post=requests.post)`
  - `Scoreboard.submit(records: list[dict]) -> bool`: ein POST mit `{"token": token, "records": records}`. Bei Fehlschlag werden alle Zeilen an die CSV angehängt und `False` zurückgegeben. Unbekannte Felder werfen `ValueError`.
  - `Scoreboard.replay_backup() -> int`: sendet alle gesicherten Zeilen in einem POST. Bei Erfolg wird die CSV gelöscht und die Anzahl zurückgegeben, sonst bleibt die CSV und das Ergebnis ist 0.

- [ ] **Step 1: Tests umschreiben.** Die vorhandenen Tests auf Listen umstellen. Neu bzw. geändert:
  - `test_submit_posts_records_in_one_request`: 2 Zeilen → genau 1 POST, `json["records"]` hat 2 Einträge.
  - `test_failure_writes_all_rows_to_csv`: 5 Zeilen, POST scheitert → CSV hat Kopfzeile + 5 Zeilen.
  - `test_replay_sends_backup_in_one_request_and_clears_it`
  - `test_replay_keeps_backup_on_failure`
  - `test_unknown_field_rejected`
  - Die Retry- und Token-Tests bleiben.
- [ ] **Step 2: Tests laufen lassen und Fehler sehen.** `python -m pytest tests/test_scoreboard.py -q`. Erwartet: FAIL.
- [ ] **Step 3: `scoreboard.py` umsetzen** wie in den Interfaces. CSV-Werte sind Strings; Apps Script wandelt Zahlen über `num()` um.
- [ ] **Step 4: Tests grün.** `python -m pytest tests/test_scoreboard.py -q`. `test_scoreboard_contract.py::test_fields_match` schlägt jetzt fehl, das ist erwartet und wird in Task 5 behoben. Bis dahin mit `@pytest.mark.xfail(reason="Code.gs folgt in Task 5", strict=True)` markieren.
- [ ] **Step 5: Commit** `feat: Scoreboard sendet Listen und kennt den neuen Datenvertrag`

### Task 3: `verbinde`, `bewerte`, `bewerte_alle`

**Files:**
- Create: `judge_lab/bausteine.py`
- Modify: `judge_lab/__init__.py`
- Test: `tests/test_bausteine.py`

**Interfaces:**
- Consumes: `join.join`, `join.ServerUnreachable`, `llm.make_client`, `llm.ConfigError`, `runner.judge`, `prompts.build_prompt(snippet, with_tests=False, custom_block=prompt)`, `matching.match_findings`, `scoring.weighted_score`, `snippets.load_snippets`/`get_snippet`, `config.*`
- Produces:
  - `verbinde(code: str = "", *, key: str = "", gruppe: str = "") -> None`. Setzt `_ZUSTAND = {"gruppe": str, "key": str}`.
  - `bewerte(prompt: str, snippet: str = "bank_account", modell: str = DEFAULT_MODEL) -> dict`
  - `bewerte_alle(prompt: str, modell: str = DEFAULT_MODEL) -> list[dict]`
  - Ergebnis-dict (immer alle Schlüssel): `code_score: float | None`, `judge_score: int | None`, `snippet: str`, `komplexitaet: str` (`"L1"`… oder `""`), `modell: str`, `prompt: str`, `gruppe: str`, `einreichung: str` (uuid4 hex), `fehler: str | None`.
  - Testhilfe (privat): `_ZUSTAND` und `_join = join.join` als Modulattribute, damit Tests sie per monkeypatch ersetzen können.

- [ ] **Step 1: Tests schreiben.** Alle mit `modell="mock"` bzw. gepatchtem `_join`:
  ```python
  def test_verbinde_sets_group(monkeypatch, capsys):
      monkeypatch.setattr(bausteine, "_join", lambda code, **kw: ("Gruppe 2", "sk-x"))
      bausteine.verbinde(" k7qx ")
      assert bausteine._ZUSTAND == {"gruppe": "Gruppe 2", "key": "sk-x"}
      assert "Gruppe 2" in capsys.readouterr().out

  def test_verbinde_wrong_code_prints_no_traceback(monkeypatch, capsys):
      def fail(code, **kw): raise ConfigError("Code unbekannt – bitte …")
      monkeypatch.setattr(bausteine, "_join", fail)
      bausteine.verbinde("XXXX")        # wirft nicht
      assert "Code unbekannt" in capsys.readouterr().out

  def test_verbinde_notfall_with_key_and_group():
      bausteine.verbinde(key="sk-y", gruppe="Team Rot")
      assert bausteine._ZUSTAND == {"gruppe": "Team Rot", "key": "sk-y"}

  def test_verbinde_again_switches_group(monkeypatch): ...  # zweiter Code gewinnt

  def test_bewerte_mock_returns_both_scores():
      r = bewerte("Sei streng.", snippet="bank_account", modell="mock")
      assert r["fehler"] is None and r["code_score"] == 6.0 and r["judge_score"] == 1   # Mock: 1 TP, 1 FP
      assert set(r) == {"code_score", "judge_score", "snippet", "komplexitaet", "modell",
                        "prompt", "gruppe", "einreichung", "fehler"}

  def test_bewerte_unknown_snippet_lists_valid_names():
      r = bewerte("x", snippet="quicksort", modell="mock")
      assert r["code_score"] is None and "qb_quicksort" in r["fehler"]

  def test_bewerte_without_verbinde_gives_hint(): # _ZUSTAND leer, modell=DEFAULT_MODEL
      r = bewerte("x")
      assert "verbinde" in r["fehler"] and r["judge_score"] is None

  def test_bewerte_empty_prompt(): assert "leer" in bewerte("  ", modell="mock")["fehler"]

  def test_bewerte_llm_error_is_not_zero(monkeypatch):     # Client liefert LLMResult(error=…)
      ...; assert r["judge_score"] is None and r["fehler"]

  def test_bewerte_missing_dimension_keeps_judge_score(monkeypatch):  # Review Focus 3
      # Fake-Client liefert JSON mit Findings, aber scores ohne "readability"
      ...; assert r["code_score"] is None and r["judge_score"] is not None and r["fehler"] is None

  def test_bewerte_uses_no_tests_in_prompt(monkeypatch): # build_prompt wird mit with_tests=False gerufen

  def test_bewerte_alle_five_snippets_sorted_and_one_submission():
      rs = bewerte_alle("Sei streng.", modell="mock")
      assert [r["komplexitaet"] for r in rs] == ["L1", "L2", "L3", "L4", "L5"]
      assert [r["snippet"] for r in rs] == ["qb_bitcount", "qb_quicksort", "qb_levenshtein",
                                            "qb_shunting_yard", "qb_next_permutation"]
      assert len({r["einreichung"] for r in rs}) == 1

  def test_bewerte_alle_one_failure_keeps_others():
      rs = bewerte_alle("x", modell="mock")   # Mock: qb_levenshtein liefert immer kaputtes JSON
      assert rs[2]["fehler"] and all(r["fehler"] is None for i, r in enumerate(rs) if i != 2)

  def test_public_api_is_exactly_four():
      import judge_lab
      assert sorted(n for n in dir(judge_lab) if not n.startswith("_") and callable(getattr(judge_lab, n))) \
             == ["bewerte", "bewerte_alle", "sende", "verbinde"]
  ```
  Eine autouse-Fixture setzt `_ZUSTAND` vor jedem Test auf `{"gruppe": "", "key": ""}`. `test_public_api_is_exactly_four` braucht `sende` und bleibt bis Task 4 rot. Darum mit `xfail(strict=True)` markieren und in Task 4 entfernen.
- [ ] **Step 2: Tests laufen lassen und Fehler sehen.** `python -m pytest tests/test_bausteine.py -q`. Erwartet: FAIL (Modul fehlt).
- [ ] **Step 3: `bausteine.py` umsetzen.**
  - `verbinde`: ruft `_join(code, url=SCOREBOARD_URL, token=SCOREBOARD_TOKEN)` auf. Gibt bei Erfolg `✅ Verbunden als {gruppe}.` aus, bei `ConfigError` `❌ {Meldung}` und lässt den Zustand dann unverändert. Mit `key` und `gruppe` ohne Code wird direkt gesetzt. Fehlt eines der beiden, kommt ein Hinweis.
  - `bewerte`: Ablauf wie in der Spec. `judge_score = POINTS["tp"]*tp + POINTS["fp_bug"]*fp`. Jeder Fehler wird zu `fehler` (deutsch) plus `print(f"⚠️ {snippet}: {fehler}")`. Bei kaputtem JSON: „Die Antwort des Modells war nicht lesbar – bitte noch einmal versuchen.“ Bei `result.error`: „Das Modell war nicht erreichbar oder hat abgelehnt ({Kurzgrund}). Key, Guthaben oder Modellname prüfen.“
  - `bewerte_alle`: gemeinsame `einreichung` und `ThreadPoolExecutor(max_workers=CONCURRENCY)`. Nach jedem fertigen Snippet `print(f"{n}/5 fertig", end="\r")`. Gibt das Ergebnis in Stufenreihenfolge zurück. Intern teilt es eine private Hilfsfunktion mit `bewerte`, damit die `einreichung` gemeinsam ist.
  - `__init__.py`: `from judge_lab.bausteine import bewerte, bewerte_alle, verbinde` und `__all__`.
- [ ] **Step 4: Tests grün.** `python -m pytest -q`. Erwartet: PASS bis auf das markierte xfail.
- [ ] **Step 5: Commit** `feat: verbinde, bewerte und bewerte_alle`

### Task 4: `sende`

**Files:**
- Modify: `judge_lab/bausteine.py`, `judge_lab/__init__.py`
- Test: `tests/test_bausteine.py`

**Interfaces:**
- Consumes: `Scoreboard`, `RECORD_FIELDS` (Task 2), Ergebnis-dict (Task 3)
- Produces: `sende(ergebnis: dict | list[dict], runde: int) -> bool`. Ergibt `True`, wenn mindestens eine Zeile angenommen wurde. Privat: `_scoreboard()` (lazy, gecacht) als patchbarer Punkt.

- [ ] **Step 1: Tests schreiben** (Fake-`Scoreboard` mit Listen-Recorder):
  - `test_sende_round2_single_result`: 1 Zeile, Felder genau `RECORD_FIELDS`, `runde == 2`, `run_id` gesetzt, `timestamp` als ISO in UTC.
  - `test_sende_round4_list_sends_five_in_one_call`
  - `test_sende_wrong_shape_for_round`: Liste in Runde 1 → nichts gesendet, Hinweis enthält „bewerte“. Einzelnes dict in Runde 3 → Hinweis enthält „bewerte_alle“.
  - `test_sende_invalid_round`: `runde=5` und `runde="2"` → nichts gesendet, Hinweis „1–4“.
  - `test_sende_skips_failed_and_reports`: 5er-Liste mit 1 Fehler → 4 gesendet, Meldung nennt das Snippet.
  - `test_sende_skips_mock`: Ergebnis mit `modell == "mock"` → nichts gesendet, Meldung „Mock-Ergebnisse gehen nicht ans Dashboard“.
  - `test_sende_replays_backup_first` (Review Focus 2): Echtes `Scoreboard` mit `tmp_path`. Erster `sende` scheitert → CSV mit 5 Zeilen. Zweiter `sende` mit funktionierendem POST → CSV leer, insgesamt 6 Zeilen angekommen.
  - `test_sende_offline_message`: Fehlschlag → Rückgabe `False`, Ausgabe enthält „lokal gesichert“.
  - Bei `test_public_api_is_exactly_four` das xfail entfernen.
- [ ] **Step 2: Tests laufen lassen und Fehler sehen.** `python -m pytest tests/test_bausteine.py -q`. Erwartet: FAIL.
- [ ] **Step 3: `sende` umsetzen.** Zuerst `replay_backup()`, dann `submit(rows)`. Meldungen: `✅ {n} Ergebnis(se) gesendet – das Dashboard zeigt es in ein paar Sekunden.` bzw. `⚠️ Dashboard nicht erreichbar – lokal gesichert, wird beim nächsten Senden nachgeholt.`
- [ ] **Step 4: Tests grün.** `python -m pytest -q`. Erwartet: alles PASS außer dem xfail aus Task 2.
- [ ] **Step 5: Commit** `feat: sende schickt Ergebnisse ans Dashboard`

### Task 5: Apps Script – Empfang, Join, Aggregation

**Files:**
- Modify (neu schreiben): `scoreboard/Code.gs`, `scoreboard/aggregate.test.mjs`
- Test: `tests/test_scoreboard_contract.py` (xfail entfernen)

**Interfaces:**
- Consumes: `RECORD_FIELDS` aus Task 2. Die JS-Konstante `FIELDS` ist dieselbe Liste **plus `"session_id"` am Ende**. Der Vertragstest prüft `FIELDS[:-1] == RECORD_FIELDS` und `FIELDS[-1] == "session_id"`.
- Produces (für Task 6):
  ```
  aggregate(rows, keyRows, joins, sessionId) → {
    session, groups: [string],            // aktive Gruppen aus keys in Reihenfolge, dann weitere aus rows
    connected: {group: bool},             // Join in dieser Session
    rounds: {
      "1"|"2": {group: Tile|null},
      "3":     {group: Curve|null},
      "4":     {group: Total|null},
    },
    leaders: [group]                      // Runde 4: alle Gruppen mit max. judge_score; [] wenn keine Daten
  }
  Tile  = {judge_score, code_score, prompt, snippet, modell, timestamp}
  Curve = {prompt, modell, timestamp, points: [{komplexitaet, snippet, code_score, judge_score}]}   // nach L1→L5
  Total = {judge_score /*Summe*/, code_score /*Ø, 2 Nachkommastellen, nur Zahlen*/, n, prompt, modell, timestamp}
  ```
  - `doPost`: `{token, records: [...]}`. Prüft das Token, setzt `session_id` aus `config`, nimmt einen Lock und schreibt mit `appendRow` je Zeile über `cellValue`. Ist `runs` leer, wird zuerst die Kopfzeile geschrieben.
  - `doGet`: `?action=join` (protokolliert mit `config.session_id`), `?format=json` → `getData()`, sonst `dashboard.html` ohne Template-Variablen.
  - `getData()`: liest `runs`, `keys` und `joins` und ruft `aggregate`.
  - Behalten: `cellValue`, `num`, `normalizeCode`, `joinLookup` samt Tests. Entfernen: Phasen, Admin, Defects, Paper, Spearman, Heatmaps, `POINTS`, `STRICT_VS_LENIENT`, `GROUP_NAMES`.
- „Zuletzt“ = größter `timestamp` (ISO-Strings vergleichbar). Runde 3/4: zuerst die Einreichung mit dem neuesten `timestamp` bestimmen, dann alle Zeilen dieser `einreichung`.

- [ ] **Step 1: Node-Tests schreiben** in `aggregate.test.mjs`:
  - `"Runde 2 zeigt die neueste Zeile je Gruppe"`
  - `"doppelte run_id zählt einmal"` (Review Focus 1)
  - `"andere session_id wird ignoriert"`
  - `"Runde 3 nimmt nur die neueste Einreichung, sortiert L1–L5"`
  - `"Runde 4 summiert judge_score, mittelt code_score und ignoriert leere Werte"` (Review Focus 3): Scores `[2, 3, 1, "", 0]`/Codes `[8, 6, "", 4, 2]` → `judge_score 6`, `code_score 5`, `n 5`
  - `"leaders enthält bei Gleichstand beide Gruppen"`
  - `"Gruppen aus keys zuerst, inaktive nicht, fremde aus rows hinten"` (Review Focus 4)
  - `"connected nur für Joins der aktiven Session"`
  - `"ohne Daten: alle Kacheln null"`
  - Der Test `cellValue` für `=`, `+`, `-` und `@` wird übernommen (Review Focus 5), die `joinLookup`-Tests ebenso.
- [ ] **Step 2: Tests laufen lassen und Fehler sehen.** `node --test scoreboard/aggregate.test.mjs`. Erwartet: FAIL.
- [ ] **Step 3: `Code.gs` neu schreiben** wie in den Interfaces. Den Kopfkommentar auf die Tabs `runs`, `config` (token, session_id), `keys` und `joins` anpassen. `module.exports = { aggregate, cellValue, joinLookup, normalizeCode, FIELDS }`.
- [ ] **Step 4: Vertragstest anpassen und xfail entfernen.**
- [ ] **Step 5: Alle Tests grün.** `node --test scoreboard/aggregate.test.mjs && python -m pytest -q`. Erwartet: PASS, kein xfail mehr.
- [ ] **Step 6: Commit** `feat: Apps Script aggregiert Kacheln je Runde`

### Task 6: Dashboard und Vorschau

**Files:**
- Modify (neu schreiben): `scoreboard/dashboard.html`, `tools/dashboard_preview.mjs`

**Interfaces:**
- Consumes: Rückgabe von `aggregate` (Task 5)
- Produces: `node tools/dashboard_preview.mjs <ordner>` schreibt `runde-1.html` … `runde-4.html` mit Beispieldaten (4 Gruppen, eine davon ohne Daten, eine nur verbunden). Der Seitentitel meldet „OVERFLOW“ oder „OK“ wie bisher.

- [ ] **Step 1: `dashboard.html` umsetzen** nach dem abgestimmten Entwurf (Spec, Abschnitt Dashboard):
  - Kopfzeile mit Titel und Session, Reiter `1 Frei · 2 Rollen · 3 Komplexität · 4 AI Challenge`, Tasten 1–4.
  - Kacheln im 2×2-Raster. Runden 1, 2 und 4 zeigen Judge- und Code-Score groß, den Prompt (gekürzt, ganzer Text per `title`-Tooltip und Klick zum Aufklappen) und darunter klein „Snippet · Modell · vor x min“. Runde 4 zeigt zusätzlich „n/5 Snippets“, Leader werden hervorgehoben.
  - Runde 3: je Kachel ein Chart.js-Liniendiagramm mit zwei Y-Achsen (links Code-Score 0–10, rechts Judge-Score), X-Beschriftung „L1“ + Snippet-Name.
  - Leere Kachel ausgegraut mit „noch nichts gesendet“, bei Verbindung „verbunden – noch nichts gesendet“. `null`-Scores werden als „–“ angezeigt.
  - Laden über `google.script.run.getData()` alle 10 s. Ist `window.PREVIEW_DATA` gesetzt, wird stattdessen das gerendert, die Startrunde kommt aus `window.INITIAL_VIEW`.
  - Beamertauglich: helles Theme, Schrift ≥ 18 px, kein horizontales Scrollen bei 1280 × 720. Chart.js auf eine exakte Version pinnen (`chart.js@4.4.1`).
  - Alle Texte aus den Daten mit `esc()` escapen.
- [ ] **Step 2: `tools/dashboard_preview.mjs` umschreiben.** Die Beispielzeilen laufen durch das echte `aggregate`.
- [ ] **Step 3: Vorschau erzeugen und prüfen.** `node tools/dashboard_preview.mjs /tmp/preview` (bzw. Scratchpad), dann für jede Runde `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --window-size=1280,720 --screenshot=… file://…/runde-N.html` und `--dump-dom | grep '<title>'`. Erwartet: viermal „OK“. Die Screenshots ansehen: Kacheln, Diagramm mit zwei Achsen und Hervorhebung des Leaders sind sichtbar. Die Screenshots nicht committen.
- [ ] **Step 4: Alle Tests grün.** `node --test scoreboard/aggregate.test.mjs && python -m pytest -q`.
- [ ] **Step 5: Commit** `feat: Kachel-Dashboard für die vier Runden`

### Task 7: Doku auf zwei Anleitungen reduzieren

**Files:**
- Delete: `docs/CONCEPT.md`, `docs/GUIDE_INSTRUCTOR.md`, `docs/GUIDE_STUDENTS.md`, `docs/RUNBOOK.md`, `docs/plans/` (ganz), `docs/superpowers/specs/2026-10-31-judge-lab-design.md`, `docs/superpowers/plans/2026-10-31-judge-lab.md`, `scoreboard/DEPLOY.md`
- Create: `docs/BAUSTEINE.md`, `docs/DASHBOARD_TEST.md`
- Modify: `README.md`, Code-Kommentare mit Verweisen auf gelöschte Dateien
- Keep: `prompts/ADAPTATION.md`, `prompts/original/`, `THIRD_PARTY_NOTICES.md`, `LICENSE`

- [ ] **Step 1: `docs/BAUSTEINE.md` schreiben** (für Jessica). Inhalt laut Spec, Abschnitt „Was neu entsteht“:
  - Setup-Zelle zum Kopieren: klont `main` nach `/content/software-quality-engineering`, `pip install -q -e`, ist idempotent. Vorbild ist die erste Code-Zelle in `notebooks/hands_on.ipynb`, diese **nur lesen**. Darin auch der Import der vier Funktionen.
  - Je Funktion: Zweck, Parameter, Rückgabe.
  - Ein Beispiel je Runde: Runde 1 `bewerte` + `sende(…, runde=1)`, Runde 2 zwei Rollen-Prompts nacheinander, Runde 3 und 4 `bewerte_alle` + `sende`.
  - Tabelle der Snippet-Namen mit Stufe, Hinweis auf die Haltungsvorlagen in `prompts/attitudes/`.
  - Was die Studierenden bei Fehlern sehen.
  - Ein Absatz „Was im Hintergrund passiert“.
  - Höchstens 2 Seiten.
- [ ] **Step 2: `docs/DASHBOARD_TEST.md` schreiben** (für Eva):
  - Einrichtung: Sheet, Tabs `config` (token, session_id), `keys` (code | group | openrouter_key | active) und `joins`. Einen alten `runs`-Tab vorher in `runs_alt` umbenennen.
  - Apps Script neu deployen und URL/Token in `config.py` eintragen (aus `DEPLOY.md` übernehmen, gekürzt).
  - Testablauf mit `notebooks/eva_test.ipynb`: alle vier Runden senden, je Runde die Kachel am Dashboard prüfen (Checkliste).
  - Offline-Probe: `SCOREBOARD_URL` leer, dann CSV prüfen.
  - Danach `session_id` im Tab `config` auf `live` setzen.
  - Layout ohne Deploy prüfen: `node tools/dashboard_preview.mjs`.
- [ ] **Step 3: `README.md` auf ≤ 15 Zeilen kürzen.** Was das Repo ist, Links auf beide Anleitungen und die lokale Entwicklung (`uv venv`, `pip install -e ".[dev]"`, `pytest`). Keine Colab-Badges auf alte Notebooks.
- [ ] **Step 4: Alte Doku löschen** (Liste oben) und tote Verweise finden: `grep -rnE "CONCEPT|RUNBOOK|GUIDE_|DEPLOY\.md|OFFENE_FRAGEN|role_cards" judge_lab scoreboard tools tests prompts README.md THIRD_PARTY_NOTICES.md docs`. Erwartet: keine Treffer außer in `docs/superpowers/` (Spec und Plan).
- [ ] **Step 5: Tests grün.** `python -m pytest -q`.
- [ ] **Step 6: Commit** `docs: nur noch Anleitungen für Jessica und das Dashboard`

### Task 8: Test-Notebook für Eva (nicht committen)

**Files:**
- Create: `notebooks/eva_test.ipynb`
- Modify: `.git/info/exclude` (lokal, nicht versioniert)

- [ ] **Step 1: `notebooks/eva_test.ipynb` per Skript erzeugen** (nbformat 4, Python-3-Kernel). Die Zellen:
  - Setup über den lokalen Checkout (`sys.path` auf das Repo-Root) und Import der vier Funktionen.
  - `verbinde("CODE")` mit dem Platzhalter `"CODE"`.
  - Zuerst eine Mock-Probe ohne Senden: `bewerte(…, modell="mock")`.
  - Runde 1: `bewerte` + `sende(…, 1)`.
  - Runde 2: zwei Prompts aus `prompts/attitudes/strict.md` und `lenient.md`, beide gesendet.
  - Runde 3: `bewerte_alle` + `sende(…, 3)`.
  - Runde 4: `bewerte_alle` + `sende(…, 4)`.
- [ ] **Step 2: Lokal ignorieren.** `echo "notebooks/eva_test.ipynb" >> .git/info/exclude`.
- [ ] **Step 3: Prüfen.** `git status --porcelain notebooks/`. Erwartet: `eva_test.ipynb` taucht nicht auf, und keine Datei in `notebooks/` ist geändert (`git diff --stat main -- notebooks/` zeigt nur, was schon vor diesem Plan auf dem Branch war).
- [ ] **Step 4: Mock-Durchlauf.** `python -c` mit den Mock-Zellen (ohne `sende`). Erwartet: dicts mit beiden Scores, kein Traceback.
- Kein Commit.

### Task 9: Abschluss und Merge nach `main`

- [ ] **Step 1: Komplettlauf.** `python -m pytest -q && node --test scoreboard/aggregate.test.mjs`. Erwartet: alles PASS.
- [ ] **Step 2: Notebooks unberührt?** `git diff --stat d47084e -- notebooks/ tools/build_notebooks.py`. Erwartet: leer.
- [ ] **Step 3: Live-Probe durch Eva** (braucht echten Code und deployte Web-App): `eva_test.ipynb` nach `docs/DASHBOARD_TEST.md` durchlaufen. Erst danach weiter.
- [ ] **Step 4: Merge nach `main`** über superpowers:finishing-a-development-branch. Vor dem Merge und vor jedem Push bei Eva nachfragen.
