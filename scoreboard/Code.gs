/**
 * Scoreboard für das Hands-on „LLM-as-a-Judge“ (Google Apps Script, V8).
 *
 * Tabs im Sheet:
 *   runs    – eine Zeile pro bewertetem Snippet, Kopfzeile = FIELDS (wird automatisch angelegt)
 *   config  – Schlüssel/Wert-Paare: token, session_id (aktive Session)
 *   keys    – Gruppencodes: code | group | openrouter_key | active (privat, nur dieses Skript liest ihn)
 *   joins   – erfolgreiche Joins: timestamp | session_id | group (wird automatisch angelegt)
 *
 * doPost – nimmt Ergebnisse an: {token, records: [...]}; session_id setzt das Skript aus config
 * doGet  – ohne Parameter: Dashboard; ?format=json: aggregierte Daten;
 *          ?action=join&code=…&token=…: Gruppe und Key zum Gruppencode
 */

// Gleiche Reihenfolge wie RECORD_FIELDS in judge_lab/scoreboard.py, plus session_id
// (Test: tests/test_scoreboard_contract.py)
const FIELDS = [
  "timestamp",
  "run_id",
  "gruppe",
  "runde",
  "snippet",
  "komplexitaet",
  "modell",
  "prompt",
  "code_score",
  "judge_score",
  "einreichung",
  "session_id"
];

const ROUNDS = ["1", "2", "3", "4"];
const NUMBER_FIELDS = ["runde", "code_score", "judge_score"];

// --- Hilfsfunktionen ----------------------------------------------------------

function num(value) {
  if (value === "" || value === null || value === undefined) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/**
 * Wert für das Sheet. Text, der mit = + - @ beginnt (z. B. ein Prompt mit Markdown-Aufzählung),
 * würde Sheets sonst als Formel auswerten; das vorangestellte ' speichert ihn als Text.
 */
function cellValue(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "string" && /^[=+\-@]/.test(value)) return "'" + value;
  return value;
}

function bool(value) {
  return value === true || String(value).toLowerCase() === "true";
}

/** Sheets wandelt ISO-Zeitstempel oft in Date-Objekte um; beide Formen werden vergleichbar. */
function timeMs(value) {
  if (value instanceof Date) return value.getTime();
  const t = Date.parse(String(value));
  return Number.isNaN(t) ? 0 : t;
}

function latest(rows) {
  return rows.reduce((best, r) => (best === null || timeMs(r.timestamp) >= timeMs(best.timestamp) ? r : best), null);
}

function isoTime(value) {
  const t = timeMs(value);
  return t ? new Date(t).toISOString() : "";
}

/**
 * Zeile für setValues. Zahlenfelder als Zahl (auch aus der CSV-Sicherung, die nur Text kennt);
 * alles andere als Text mit vorangestelltem ' – sonst macht ein deutsches Sheet aus „5.2“ ein Datum,
 * aus einem ISO-Zeitstempel eine Ortszeit und aus „=…“ eine Formel.
 */
function rowValues(record, sessionId) {
  return FIELDS.map((f) => {
    const value = f === "session_id" ? sessionId : record[f];
    if (NUMBER_FIELDS.indexOf(f) >= 0) {
      const n = num(value);
      return n === null ? "" : n;
    }
    return value === null || value === undefined || value === "" ? "" : "'" + String(value);
  });
}

/** Passt eine vorhandene Kopfzeile im Tab runs zu FIELDS? (Leerer Tab: ja) */
function headerMatches(header) {
  if (!header || !header.length || header.every((h) => h === "")) return true;
  return header.length === FIELDS.length && FIELDS.every((f, i) => String(header[i]) === f);
}

// --- Aggregation (reine Funktion, mit Node getestet) ----------------------------

function tile(rows) {
  const r = latest(rows);
  return { judge_score: num(r.judge_score), code_score: num(r.code_score), prompt: String(r.prompt),
           snippet: String(r.snippet), modell: String(r.modell), timestamp: isoTime(r.timestamp) };
}

/** Alle Zeilen der neuesten Einreichung, je Snippet nur die neueste (doppelt gesendet zählt einmal). */
function latestSubmission(rows) {
  const newest = latest(rows);
  const bySnippet = {};
  rows.filter((r) => String(r.einreichung) === String(newest.einreichung)).forEach((r) => {
    const key = String(r.snippet);
    if (!bySnippet[key] || timeMs(r.timestamp) >= timeMs(bySnippet[key].timestamp)) bySnippet[key] = r;
  });
  return Object.keys(bySnippet).map((k) => bySnippet[k]);
}

function curveTile(rows) {
  const subset = latestSubmission(rows);
  const head = latest(subset);
  const points = subset
    .map((r) => ({ komplexitaet: String(r.komplexitaet), snippet: String(r.snippet),
                   code_score: num(r.code_score), judge_score: num(r.judge_score) }))
    .sort((a, b) => a.komplexitaet.localeCompare(b.komplexitaet));
  return { prompt: String(head.prompt), modell: String(head.modell), timestamp: isoTime(head.timestamp), points };
}

function totalTile(rows) {
  const subset = latestSubmission(rows);
  const head = latest(subset);
  const judge = subset.map((r) => num(r.judge_score)).filter((v) => v !== null);
  const code = subset.map((r) => num(r.code_score)).filter((v) => v !== null);
  return {
    judge_score: judge.length ? judge.reduce((a, b) => a + b, 0) : null,
    code_score: code.length ? Math.round((code.reduce((a, b) => a + b, 0) / code.length) * 100) / 100 : null,
    n: subset.length,
    prompt: String(head.prompt),
    modell: String(head.modell),
    timestamp: isoTime(head.timestamp),
  };
}

function aggregate(rows, keyRows, joins, sessionId) {
  const session = String(sessionId || "");
  const seen = {};
  const live = (rows || []).filter((r) => {
    if (String(r.session_id) !== session) return false;
    const id = String(r.run_id || "");
    if (!id) return true;
    if (seen[id]) return false;
    seen[id] = true;
    return true;
  });

  const groups = [];
  (keyRows || []).forEach((k) => {
    const g = String(k.group || "").trim();
    if (g && bool(k.active) && groups.indexOf(g) < 0) groups.push(g);
  });
  live.forEach((r) => {
    const g = String(r.gruppe || "").trim();
    if (g && groups.indexOf(g) < 0) groups.push(g);
  });

  const connected = {};
  groups.forEach((g) => {
    connected[g] = (joins || []).some((j) => String(j.group) === g && String(j.session_id) === session);
  });

  const rounds = {};
  ROUNDS.forEach((round) => {
    rounds[round] = {};
    groups.forEach((g) => {
      const mine = live.filter((r) => String(num(r.runde)) === round && String(r.gruppe).trim() === g);
      if (!mine.length) rounds[round][g] = null;
      else if (round === "3") rounds[round][g] = curveTile(mine);
      else if (round === "4") rounds[round][g] = totalTile(mine);
      else rounds[round][g] = tile(mine);
    });
  });

  const scores = groups.map((g) => (rounds["4"][g] ? rounds["4"][g].judge_score : null)).filter((v) => v !== null);
  const best = scores.length ? Math.max.apply(null, scores) : null;
  const leaders = best === null ? [] : groups.filter((g) => rounds["4"][g] && rounds["4"][g].judge_score === best);

  return { session, groups, connected, rounds, leaders };
}

// --- Gruppencodes (reine Funktion, mit Node getestet) ----------------------------

function normalizeCode(value) {
  return String(value === null || value === undefined ? "" : value).replace(/\s+/g, "").toUpperCase();
}

/** Antwort auf ?action=join. Ohne gültiges Token gibt es keinen Key, auch nicht bei leerem Token im Sheet. */
function joinLookup(keyRows, config, params) {
  if (!config.token || params.token !== config.token) return { status: "error", message: "Ungültiges Token" };
  const code = normalizeCode(params.code);
  const row = code && keyRows.find((r) => normalizeCode(r.code) === code && bool(r.active));
  if (!row) return { status: "error", message: "Code unbekannt" };
  return { status: "ok", group: String(row.group), key: String(row.openrouter_key) };
}

// --- Apps Script: Sheet-Zugriff -------------------------------------------------

function sheet_(name) {
  const book = SpreadsheetApp.getActiveSpreadsheet();
  return book.getSheetByName(name) || book.insertSheet(name);
}

function config_() {
  const values = sheet_("config").getDataRange().getValues();
  const result = {};
  values.forEach((row) => {
    if (row[0]) result[String(row[0]).trim()] = String(row[1]).trim();
  });
  return result;
}

function readTable_(name) {
  const values = sheet_(name).getDataRange().getValues();
  if (values.length < 2) return [];
  const header = values[0].map(String);
  return values.slice(1).map((row) => Object.fromEntries(header.map((key, i) => [key, row[i]])));
}

/** Protokolliert einen erfolgreichen Join (für „verbunden“ im Dashboard); ohne Key. */
function logJoin_(sessionId, group) {
  const joins = sheet_("joins");
  if (joins.getLastRow() === 0) joins.appendRow(["timestamp", "session_id", "group"]);
  joins.appendRow([new Date().toISOString(), cellValue(sessionId), cellValue(group)]);
}

function json_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  let body;
  try {
    body = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ status: "error", message: "Kein gültiges JSON" });
  }
  const config = config_();
  if (!body || !config.token || body.token !== config.token) {
    return json_({ status: "error", message: "Ungültiges Token" });
  }
  if (!Array.isArray(body.records) || !body.records.length) {
    return json_({ status: "error", message: "Keine Ergebnisse (records) im Request" });
  }

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const runs = sheet_("runs");
    if (runs.getLastRow() === 0) runs.appendRow(FIELDS);
    const header = runs.getRange(1, 1, 1, runs.getLastColumn()).getValues()[0];
    if (!headerMatches(header)) {
      return json_({ status: "error", message: "Tab runs hat eine alte Kopfzeile – bitte in runs_alt umbenennen" });
    }
    const values = body.records.map((record) => rowValues(record, config.session_id || ""));
    runs.getRange(runs.getLastRow() + 1, 1, values.length, FIELDS.length).setValues(values);
    return json_({ status: "ok", records: values.length });
  } finally {
    lock.releaseLock();
  }
}

/** Wird vom Dashboard über google.script.run aufgerufen. */
function getData() {
  const config = config_();
  return aggregate(readTable_("runs"), readTable_("keys"), readTable_("joins"), config.session_id);
}

function doGet(e) {
  const params = (e && e.parameter) || {};
  if (params.action === "join") {
    const config = config_();
    const answer = joinLookup(readTable_("keys"), config, params);
    if (answer.status === "ok") logJoin_(config.session_id || "", answer.group);
    return json_(answer);
  }
  if (params.format === "json") {
    return json_(getData());
  }
  return HtmlService.createHtmlOutputFromFile("dashboard")
    .setTitle("Scoreboard – LLM-as-a-Judge")
    .addMetaTag("viewport", "width=device-width, initial-scale=1");
}

// Für die Tests mit Node; in Apps Script ist `module` nicht definiert.
if (typeof module !== "undefined") module.exports = { aggregate, cellValue, headerMatches, joinLookup, normalizeCode, rowValues, FIELDS };
