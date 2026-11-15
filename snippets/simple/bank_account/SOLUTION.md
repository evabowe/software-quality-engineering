# bank_account – Lösung

> **Achtung, Lösung:** Diese Datei beschreibt die eingebauten Defekte. Sie wird im Hands-on-Notebook nie angezeigt und darf nicht in einen Judge-Prompt gelangen.

## Tests ausführen: pytest verwenden

Die Tests laufen mit **pytest**. Sie schlagen absichtlich fehl (siehe unten) und gehören deshalb nicht zur normalen Testsuite des Projekts.

Einmalig einrichten:
1. `pip install pytest`
2. In PyCharm: **Settings → Tools → Python Integrated Tools → Default test runner: pytest**

Im Terminal aus diesem Ordner heraus: `python -m pytest tests.py`. Die Projekt-Testsuite prüft zusätzlich automatisch, dass genau die unten dokumentierten Tests fehlschlagen (`tests/test_ground_truth.py`).

## Eingebaute Fehler

### bank_account.py – semantische Fehler

| # | Methode / Zeile | Fehler (Code) | Richtig wäre | Auswirkung |
|---|---|---|---|---|
| 1 | `deposit`, Z. 26 | `self.balance -= amount` | `self.balance += amount` | Einzahlen verringert den Kontostand. |
| 2 | `withdraw`, Z. 31 | `if self.balance - amount <= -self.overdraft_limit:` | `<` statt `<=` | Abheben genau bis zum Dispo-Limit (z. B. auf −200 bei Limit 200) wird abgelehnt, obwohl es erlaubt ist. |
| 3 | `transfer`, Z. 39–40 | erst `target.deposit(amount)`, dann `self.withdraw(amount)` | erst abbuchen, dann gutschreiben | Scheitert die Abbuchung (z. B. Dispo überschritten), hat der Empfänger das Geld trotzdem schon erhalten. |

Fehlschlagende Tests (4 von 20):

| Test | Ursache |
|---|---|
| `TestDeposit::test_deposit_increases_balance` | Fehler 1 |
| `TestWithdraw::test_withdraw_exactly_to_limit_is_allowed` | Fehler 2 |
| `TestTransfer::test_failed_transfer_changes_nothing` | Fehler 3 |
| `TestTransfer::test_transfer_moves_money` | Folgefehler von Fehler 1 (die Gutschrift beim Empfänger nutzt `deposit`) |

### bank_account.py – programmatische Fehler (Code-Qualität)

Diese Fehler ändern das Verhalten nicht und lassen keinen Test fehlschlagen. Sie sind toter bzw. überflüssiger Code und eher ein Fall für statische Analyse (z. B. SonarQube for IDE, PyCharm-Inspektionen, ruff/pylint) oder ein Code-Review.

| # | Methode / Zeile | Fehler (Code) | Richtig wäre | Problem |
|---|---|---|---|---|
| 4 | `deposit`, Z. 24–25 | `elif amount < 0:` / `amount = abs(amount)` | Zweig entfernen | Toter Zweig: Jeder negative Betrag erfüllt schon `amount <= 0` und löst vorher den Fehler aus. Die Bedingung ist logisch enthalten, aber nicht identisch, daher wird sie von Tools vermutlich nicht erkannt. |
| 5 | `withdraw`, Z. 33 | `self.balance = self.balance` direkt nach `raise` | Zeile entfernen | Unerreichbarer Code: Nach `raise` wird nichts mehr ausgeführt (zusätzlich ist die Zuweisung wirkungslos). |
| 6 | `apply_interest`, Z. 42 | Parameter `days=30` | Parameter entfernen | Ungenutzter Parameter: `days` wird nie verwendet und täuscht vor, dass die Zinsen von der Anzahl der Tage abhängen. |
