/**
 * Scoreboard für das Hands-on „LLM-as-a-Judge“ (Google Apps Script, V8).
 *
 * Tabs im Sheet:
 *   runs     – eine Zeile pro LLM-Lauf, Kopfzeile = FIELDS (wird automatisch angelegt)
 *   config   – Schlüssel/Wert-Paare: token, session_id (aktive Session)
 *   defects  – Ground Truth, per Upload aus dem Instructor-Notebook (für RQ1-Matrix und Auflösung)
 *
 * doPost  – nimmt Läufe ({token, record}) oder die Ground Truth ({token, defects}) an
 * doGet   – ohne Parameter: Dashboard; ?format=json[&session=…][&precomputed=1]: aggregierte Daten
 */

// Gleiche Reihenfolge wie RECORD_FIELDS in judge_lab/scoreboard.py (Test: tests/test_scoreboard_contract.py)
const FIELDS = [
  "timestamp",
  "session_id",
  "group",
  "phase",
  "model_key",
  "model_id",
  "attitude",
  "snippet_id",
  "complexity_level",
  "with_tests",
  "prompt_hash",
  "prompt_text",
  "submission_no",
  "tp",
  "fp",
  "neutral",
  "n_defects",
  "recall",
  "precision",
  "weighted_score",
  "llm_overall_score",
  "scores_json",
  "found_defect_ids",
  "findings_json",
  "parse_ok",
  "error",
  "latency_s",
  "tokens_in",
  "tokens_out",
  "prediction_best_model",
  "prediction_strict_vs_lenient",
  "notebook_version"
];

// Gleiche Werte wie POINTS in judge_lab/config.py
const POINTS = { tp: 2, fp_bug: -1 };

const DEFECT_FIELDS = ["snippet_id", "defect_id", "kind", "lines", "description"];
const ATTITUDES = ["strict", "objective", "lenient"];
const LEVELS = ["L1", "L2", "L3", "L4", "L5"];
const PRECOMPUTED = "precomputed";

// --- Hilfsfunktionen ----------------------------------------------------------

function num(value) {
  if (value === "" || value === null || value === undefined) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/**
 * Wert für appendRow. Text, der mit = + - @ beginnt (z. B. ein Prompt mit Markdown-Aufzählung),
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

function mean(values) {
  const numbers = values.map(num).filter((v) => v !== null);
  if (!numbers.length) return null;
  return Math.round((numbers.reduce((a, b) => a + b, 0) / numbers.length) * 1000) / 1000;
}

function groupBy(rows, keyFn) {
  const groups = {};
  rows.forEach((row) => {
    const key = keyFn(row);
    (groups[key] = groups[key] || []).push(row);
  });
  return groups;
}

function uniqueSorted(values) {
  return Array.from(new Set(values)).filter((v) => v !== "").sort();
}

function ranks(values) {
  const order = values.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]);
  const result = new Array(values.length);
  let i = 0;
  while (i < order.length) {
    let j = i;
    while (j + 1 < order.length && order[j + 1][0] === order[i][0]) j++;
    const rank = (i + j) / 2 + 1; // Durchschnittsrang bei Gleichstand
    for (let k = i; k <= j; k++) result[order[k][1]] = rank;
    i = j + 1;
  }
  return result;
}

function spearman(xs, ys) {
  if (xs.length < 3) return null;
  const rx = ranks(xs);
  const ry = ranks(ys);
  const mx = rx.reduce((a, b) => a + b, 0) / rx.length;
  const my = ry.reduce((a, b) => a + b, 0) / ry.length;
  let cov = 0, vx = 0, vy = 0;
  for (let i = 0; i < rx.length; i++) {
    cov += (rx[i] - mx) * (ry[i] - my);
    vx += (rx[i] - mx) ** 2;
    vy += (ry[i] - my) ** 2;
  }
  if (vx === 0 || vy === 0) return null;
  return Math.round((cov / Math.sqrt(vx * vy)) * 1000) / 1000;
}

function heatmap(rows, models, field) {
  const result = {};
  models.forEach((model) => {
    result[model] = {};
    ATTITUDES.forEach((attitude) => {
      result[model][attitude] = mean(
        rows.filter((r) => r.model_key === model && r.attitude === attitude).map((r) => r[field])
      );
    });
  });
  return result;
}

function submissionPoints(rows) {
  return rows.reduce((sum, r) => sum + POINTS.tp * (num(r.tp) || 0) + POINTS.fp_bug * (num(r.fp) || 0), 0);
}

// --- Aggregation (reine Funktion, mit Node getestet) ----------------------------

function aggregate(rows, defects, sessionId, includePrecomputed) {
  const selected = rows.filter(
    (r) => r.session_id === sessionId || (includePrecomputed && r.session_id === PRECOMPUTED)
  );
  const a1 = selected.filter((r) => r.phase === "a1");
  const models = uniqueSorted(a1.map((r) => r.model_key));

  // RQ1: welcher Defekt wurde von welchem Modell wie oft gefunden?
  const defectByModel = defects.map((d) => {
    const rates = {};
    models.forEach((model) => {
      const runs = a1.filter((r) => r.model_key === model && r.snippet_id === d.snippet_id);
      const found = runs.filter((r) => String(r.found_defect_ids).split(",").indexOf(d.defect_id) >= 0);
      rates[model] = runs.length ? Math.round((found.length / runs.length) * 1000) / 1000 : null;
    });
    return { snippet_id: d.snippet_id, defect_id: d.defect_id, kind: d.kind, rates: rates };
  });

  // RQ1: Rangkorrelation der Scores über gemeinsame Bedingungen
  const scoreByKey = {};
  a1.forEach((r) => {
    const score = num(r.weighted_score);
    if (score === null) return;
    const key = [r.snippet_id, r.attitude, bool(r.with_tests)].join("|");
    (scoreByKey[r.model_key] = scoreByKey[r.model_key] || {})[key] = score;
  });
  const spearmanMatrix = {};
  models.forEach((a) => {
    spearmanMatrix[a] = {};
    models.forEach((b) => {
      const keys = Object.keys(scoreByKey[a] || {}).filter((k) => k in (scoreByKey[b] || {}));
      spearmanMatrix[a][b] = spearman(keys.map((k) => scoreByKey[a][k]), keys.map((k) => scoreByKey[b][k]));
    });
  });

  // RQ3 und Zusatzfaktoren
  const recallByLevel = { levels: LEVELS, series: {} };
  const testsDelta = {};
  const publicVsPrivate = {};
  const parseFailures = {};
  models.forEach((model) => {
    const own = a1.filter((r) => r.model_key === model);
    recallByLevel.series[model] = LEVELS.map((level) =>
      mean(own.filter((r) => r.complexity_level === level).map((r) => r.recall))
    );
    const withTests = own.filter((r) => bool(r.with_tests));
    const withoutTests = own.filter((r) => !bool(r.with_tests));
    testsDelta[model] = {
      recallWith: mean(withTests.map((r) => r.recall)),
      recallWithout: mean(withoutTests.map((r) => r.recall)),
      fpWith: mean(withTests.map((r) => r.fp)),
      fpWithout: mean(withoutTests.map((r) => r.fp)),
    };
    publicVsPrivate[model] = {
      quixbugs: mean(own.filter((r) => String(r.snippet_id).indexOf("qb_") === 0).map((r) => r.recall)),
      bank_account: mean(own.filter((r) => r.snippet_id === "bank_account").map((r) => r.recall)),
    };
  });
  // Formattreue über alle Phasen mit LLM-Lauf
  const llmRuns = selected.filter((r) => r.phase !== "prognosis");
  Object.entries(groupBy(llmRuns, (r) => r.model_key)).forEach(([model, runs]) => {
    parseFailures[model] = { failed: runs.filter((r) => !bool(r.parse_ok)).length, total: runs.length };
  });

  // Prognosen: je Gruppe die letzte
  const predictions = Object.values(groupBy(selected.filter((r) => r.phase === "prognosis"), (r) => r.group))
    .map((list) => list.sort((x, y) => String(x.timestamp).localeCompare(String(y.timestamp))).pop())
    .map((r) => ({ group: r.group, best_model: r.prediction_best_model, strict_vs_lenient: r.prediction_strict_vs_lenient }))
    .sort((x, y) => x.group.localeCompare(y.group));

  // Prompt-Challenge
  const challenge = selected.filter((r) => r.phase === "a2_submit" || r.phase === "reference");
  const gallery = Object.values(groupBy(challenge, (r) => r.group + "|" + r.submission_no)).map((runs) => {
    const own = runs.filter((r) => r.phase === "a2_submit");
    const reference = runs.filter((r) => r.phase === "reference");
    const text = own.map((r) => r.prompt_text).find((t) => t) || "";
    return {
      group: runs[0].group,
      model_key: own.length ? own[0].model_key : "",
      submission_no: num(runs[0].submission_no),
      prompt_hash: runs[0].prompt_hash,
      prompt_text: text,
      points: own.length ? submissionPoints(own) : null,
      reference_points: reference.length ? submissionPoints(reference) : null,
    };
  });
  const leaderboard = Object.values(groupBy(gallery.filter((g) => g.points !== null), (g) => g.group))
    .map((list) => list.sort((x, y) => y.points - x.points || x.submission_no - y.submission_no)[0])
    .sort((x, y) => y.points - x.points || x.group.localeCompare(y.group));

  return {
    session: sessionId,
    models: models,
    attitudes: ATTITUDES,
    runs: selected.length,
    scoreHeatmap: heatmap(a1, models, "weighted_score"),
    recallHeatmap: heatmap(a1, models, "recall"),
    fpHeatmap: heatmap(a1, models, "fp"),
    defectByModel: defectByModel,
    spearman: spearmanMatrix,
    recallByLevel: recallByLevel,
    testsDelta: testsDelta,
    publicVsPrivate: publicVsPrivate,
    parseFailures: parseFailures,
    predictions: predictions,
    leaderboard: leaderboard,
    gallery: gallery.sort((x, y) => x.group.localeCompare(y.group) || x.submission_no - y.submission_no),
    resolution: defects,
  };
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
  if (!body || body.token !== config_().token) {
    return json_({ status: "error", message: "Ungültiges Token" });
  }

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    if (Array.isArray(body.defects)) {
      const target = sheet_("defects");
      target.clearContents();
      target.appendRow(DEFECT_FIELDS);
      body.defects.forEach((d) => target.appendRow(DEFECT_FIELDS.map((f) => cellValue(d[f]))));
      return json_({ status: "ok", defects: body.defects.length });
    }
    const runs = sheet_("runs");
    if (runs.getLastRow() === 0) runs.appendRow(FIELDS);
    const record = body.record || {};
    runs.appendRow(FIELDS.map((f) => cellValue(record[f])));
    return json_({ status: "ok" });
  } finally {
    lock.releaseLock();
  }
}

/** Wird vom Dashboard über google.script.run aufgerufen. */
function getData(sessionId, includePrecomputed) {
  return aggregate(readTable_("runs"), readTable_("defects"), sessionId || config_().session_id, !!includePrecomputed);
}

function doGet(e) {
  const params = (e && e.parameter) || {};
  const session = params.session || config_().session_id || "";
  if (params.format === "json") {
    return json_(getData(session, params.precomputed === "1"));
  }
  const template = HtmlService.createTemplateFromFile("dashboard");
  template.session = session;
  return template
    .evaluate()
    .setTitle("Scoreboard – LLM-as-a-Judge")
    .addMetaTag("viewport", "width=device-width, initial-scale=1");
}

// Für die Tests mit Node; in Apps Script ist `module` nicht definiert.
if (typeof module !== "undefined") module.exports = { aggregate, cellValue, FIELDS, POINTS };
