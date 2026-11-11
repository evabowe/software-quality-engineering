"""Ein-Zellen-Oberfläche des Hands-on-Notebooks: nummerierte Reiter statt vieler Zellen.

``show()`` baut die Reiter aus den Panels in ``ui`` und zeigt sie an. Reiter, die
noch nicht freigegeben sind, zeigen einen Sperrtext. Der Zustand liegt in
``ui.SESSION`` und ``STATE`` auf Modulebene; ein erneutes Ausführen der Zelle
baut nur die Widgets neu.
"""

from __future__ import annotations

import html
from collections.abc import Callable
from dataclasses import dataclass, field

import ipywidgets as widgets
from IPython.display import display

from judge_lab import ui
from judge_lab.config import MODELS

TABS = ("Start", "1 Gutachten", "2 LLM-Judge", "3 Alle Beispiele", "4 Challenge", "5 Abschluss")
LAST_PHASE = len(TABS) - 1
LOCK_TEXT = "🔒 Kommt gleich – wartet auf das Signal vorne"

TIPS_STEP2 = """
<h4>Leitfragen (im Paar besprechen)</h4>
<ol>
  <li>Wo liegt euer Score im Vergleich zu den drei LLM-Haltungen?</li>
  <li>Ändert die Haltung beim LLM nur die Note – oder auch, wie viele Defekte es findet?</li>
  <li>Hat das LLM etwas gefunden, das ihr übersehen habt (oder umgekehrt)?</li>
</ol>
"""

RULES_CHALLENGE = """
<h4>Regeln</h4>
<p>Ziel sind möglichst viele echte Defekte bei möglichst wenigen Fehlalarmen
(<b>+2</b> pro Treffer, <b>−1</b> pro Fehlalarm). Probeläufe auf einem Beispiel sind unbegrenzt,
<b>Einreichungen gibt es höchstens drei</b>; sie laufen immer über alle sechs Beispiele.
Der Prompt muss allgemein funktionieren – keine Hinweise auf bestimmte Zeilen oder Funktionen.
Ihr ersetzt nur die Haltung; Skala, Aufgabe und Ausgabeformat werden automatisch angehängt.</p>
<details><summary><b>Tipps</b></summary>
<ol>
  <li><b>Rolle:</b> Gebt dem Judge eine Rolle, die <i>gründlich</i> statt <i>streng</i> ist.</li>
  <li><b>Prüfschritte:</b> Jede Bedingung, jede Schleife und jeden Rückgabewert prüfen lassen.</li>
  <li><b>Randfälle:</b> Leere Eingaben, Duplikate, Grenzwerte, Terminierung.</li>
  <li><b>Spezifikation zuerst:</b> Erst lesen, was der Code laut Docstring tun soll, dann dagegen prüfen.</li>
  <li><b>Nur sichere Befunde:</b> Fehlalarme kosten Punkte – lieber weniger, dafür begründete Befunde.</li>
</ol>
</details>
"""

CLOSING = """
<h4>Danke fürs Mitmachen!</h4>
<p>Bitte beantwortet zum Schluss noch einmal die Umfrage vom Anfang (Link auf der Folie):
<i>„Würdet ihr einem LLM das Code-Review überlassen?“</i></p>
"""


@dataclass
class AppState:
    phase: int = LAST_PHASE  # höchster freigegebener Reiter; ohne Freigabe-Server ist alles offen


STATE = AppState()


def judge_name(model_key: str) -> str:
    """Kurzname des Judges ohne Klammerzusatz, z. B. „DeepSeek“."""
    return MODELS[model_key]["label"].split(" (")[0]


def status_text() -> str:
    session = ui.SESSION
    if not session.group:
        return "Noch nicht verbunden – bitte im Reiter „Start“ den Gruppencode eingeben."
    board = "✅" if session.scoreboard and session.scoreboard.url and not session.local_only else "⚠️"
    step = f"Schritt {STATE.phase} von {LAST_PHASE}" if STATE.phase else "Start"
    return f"{session.group} · Judge: {judge_name(session.model_key)} · Scoreboard {board} · {step}"


def _block(text: str) -> widgets.HTML:
    return widgets.HTML(text)


def _panels() -> list[Callable[[], widgets.Widget]]:
    """Ein Baukasten je Reiter; gebaut wird erst beim Entsperren."""
    return [
        ui.setup_panel,
        ui.snippet_viewer,
        lambda: widgets.VBox([ui.prognosis_panel(), _block(TIPS_STEP2)]),
        ui.assignment1_panel,
        lambda: widgets.VBox([_block(RULES_CHALLENGE), ui.assignment2_panel()]),
        lambda: _block(CLOSING),
    ]


@dataclass
class AppView:
    tab: widgets.Tab
    status: widgets.HTML
    containers: list[widgets.Box]
    factories: list[Callable[[], widgets.Widget]]
    built: dict[int, widgets.Widget] = field(default_factory=dict)

    def set_phase(self, phase: int) -> None:
        """Entsperrt alle Reiter bis einschließlich ``phase``; geöffnete Reiter bleiben offen."""
        STATE.phase = max(STATE.phase, min(phase, LAST_PHASE))
        self.render()

    def render(self) -> None:
        for index, container in enumerate(self.containers):
            if index <= STATE.phase:
                if index not in self.built:
                    self.built[index] = self.factories[index]()
                    container.children = (self.built[index],)
            else:
                container.children = (_block(f"<p style='font-size:1.2em'>{LOCK_TEXT}</p>"),)
        self.refresh_status()

    def refresh_status(self) -> None:
        self.status.value = f"<div style='font-size:1.1em;padding:4px 0'><b>{html.escape(status_text())}</b></div>"


_CURRENT: AppView | None = None


def build() -> AppView:
    """Baut die Oberfläche neu (z. B. nach erneutem Ausführen der Zelle); der Zustand bleibt."""
    global _CURRENT
    containers = [widgets.VBox() for _ in TABS]
    tab = widgets.Tab(children=containers)
    for index, title in enumerate(TABS):
        tab.set_title(index, title)
    view = AppView(tab=tab, status=widgets.HTML(), containers=containers, factories=_panels())
    view.render()
    _CURRENT = view
    return view


def current() -> AppView | None:
    return _CURRENT


def show() -> None:
    view = build()
    display(widgets.VBox([view.status, view.tab]))
