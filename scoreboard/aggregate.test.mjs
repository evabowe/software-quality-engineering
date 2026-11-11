// Tests für die Aggregation des Scoreboards: node --test scoreboard/aggregate.test.mjs (läuft auch über pytest)
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { aggregate, FIELDS } = require("./Code.gs");

function run(overrides) {
  const row = Object.fromEntries(FIELDS.map((f) => [f, ""]));
  return Object.assign(row, { session_id: "live", phase: "a1", parse_ok: true, n_defects: 1 }, overrides);
}

const DEFECTS = [
  { snippet_id: "qb_bitcount", defect_id: "D1", kind: "bug", lines: "5-5", description: "x" },
  { snippet_id: "qb_shunting_yard", defect_id: "D1", kind: "bug", lines: "17-18", description: "y" },
];

test("Heatmaps mitteln Score, Recall und FP je Modell und Haltung", () => {
  const rows = [
    run({ model_key: "gemini", attitude: "strict", weighted_score: 4, recall: 1, fp: 2 }),
    run({ model_key: "gemini", attitude: "strict", weighted_score: "6", recall: "0", fp: "0" }),
    run({ model_key: "gemini", attitude: "lenient", weighted_score: 8, recall: 1, fp: 0 }),
  ];
  const data = aggregate(rows, DEFECTS, "live", false);
  assert.equal(data.scoreHeatmap.gemini.strict, 5);
  assert.equal(data.recallHeatmap.gemini.strict, 0.5);
  assert.equal(data.fpHeatmap.gemini.strict, 1);
  assert.equal(data.scoreHeatmap.gemini.lenient, 8);
  assert.deepEqual(data.models, ["gemini"]);
});

test("andere Sessions und Vorab-Daten nur mit Schalter", () => {
  const rows = [
    run({ model_key: "kimi", attitude: "strict", recall: 1 }),
    run({ model_key: "local", attitude: "strict", recall: 0, session_id: "precomputed" }),
    run({ model_key: "deepseek", attitude: "strict", recall: 0, session_id: "rehearsal-1" }),
  ];
  assert.deepEqual(aggregate(rows, DEFECTS, "live", false).models, ["kimi"]);
  assert.deepEqual(aggregate(rows, DEFECTS, "live", true).models, ["kimi", "local"]);
});

test("Recall je Stufe ignoriert Snippets ohne Stufe", () => {
  const rows = [
    run({ model_key: "gemini", attitude: "strict", complexity_level: "L1", recall: 1 }),
    run({ model_key: "gemini", attitude: "strict", complexity_level: "", snippet_id: "bank_account", recall: 0 }),
  ];
  const { recallByLevel } = aggregate(rows, DEFECTS, "live", false);
  assert.deepEqual(recallByLevel.levels, ["L1", "L2", "L3", "L4", "L5"]);
  assert.deepEqual(recallByLevel.series.gemini, [1, null, null, null, null]);
});

test("Defekt-Matrix enthält auch nie gefundene Defekte", () => {
  const rows = [
    run({ model_key: "gemini", snippet_id: "qb_bitcount", found_defect_ids: "D1" }),
    run({ model_key: "gemini", snippet_id: "qb_bitcount", found_defect_ids: "" }),
    run({ model_key: "gemini", snippet_id: "qb_shunting_yard", found_defect_ids: "" }),
  ];
  const { defectByModel } = aggregate(rows, DEFECTS, "live", false);
  assert.equal(defectByModel.length, 2);
  assert.equal(defectByModel[0].rates.gemini, 0.5);
  assert.equal(defectByModel[1].rates.gemini, 0);
});

test("mit/ohne Tests und QuixBugs/bank_account", () => {
  const rows = [
    run({ model_key: "kimi", with_tests: true, recall: 1, fp: 0, snippet_id: "qb_quicksort" }),
    run({ model_key: "kimi", with_tests: "False", recall: 0.5, fp: 2, snippet_id: "bank_account" }),
  ];
  const data = aggregate(rows, DEFECTS, "live", false);
  assert.deepEqual(data.testsDelta.kimi, { recallWith: 1, recallWithout: 0.5, fpWith: 0, fpWithout: 2 });
  assert.deepEqual(data.publicVsPrivate.kimi, { quixbugs: 1, bank_account: 0.5 });
});

test("Formattreue zählt parse_ok auch als Text", () => {
  const rows = [
    run({ model_key: "local", parse_ok: "False" }),
    run({ model_key: "local", parse_ok: "TRUE" }),
    run({ model_key: "local", parse_ok: false }),
  ];
  assert.deepEqual(aggregate(rows, DEFECTS, "live", false).parseFailures.local, { failed: 2, total: 3 });
});

test("Spearman-Korrelation der Scores zwischen Modellen", () => {
  const rows = [];
  [[2, 3], [5, 6], [8, 9]].forEach(([a, b], i) => {
    rows.push(run({ model_key: "gemini", snippet_id: "s" + i, attitude: "strict", weighted_score: a }));
    rows.push(run({ model_key: "kimi", snippet_id: "s" + i, attitude: "strict", weighted_score: b }));
  });
  const { spearman } = aggregate(rows, DEFECTS, "live", false);
  assert.equal(spearman.gemini.kimi, 1);
  assert.equal(spearman.gemini.gemini, 1);
});

test("Leaderboard nimmt die beste von drei Einreichungen", () => {
  const sub = (no, tp, fp, phase = "a2_submit") =>
    run({ group: "Gruppe 1", model_key: phase === "reference" ? "reference" : "gemini", phase,
          submission_no: no, tp, fp, prompt_text: phase === "a2_submit" ? "P" + no : "" });
  const rows = [sub(1, 1, 0), sub(2, 3, 1), sub(2, 2, 0, "reference"), sub(3, 0, 4),
                run({ group: "Gruppe 2", model_key: "kimi", phase: "a2_submit", submission_no: 1, tp: 1, fp: 0,
                      prompt_text: "Q" })];
  const { leaderboard, gallery } = aggregate(rows, DEFECTS, "live", false);
  assert.deepEqual(leaderboard.map((e) => [e.group, e.submission_no, e.points, e.reference_points]),
                   [["Gruppe 1", 2, 5, 4], ["Gruppe 2", 1, 2, null]]);
  assert.equal(gallery.length, 4);
  assert.equal(gallery.find((g) => g.group === "Gruppe 1" && g.submission_no === 2).prompt_text, "P2");
});

test("Prognosen: je Gruppe die letzte", () => {
  const rows = [
    run({ phase: "prognosis", group: "Gruppe 1", prediction_best_model: "kimi", timestamp: "1" }),
    run({ phase: "prognosis", group: "Gruppe 1", prediction_best_model: "gemini", timestamp: "2" }),
  ];
  const { predictions } = aggregate(rows, DEFECTS, "live", false);
  assert.deepEqual(predictions.map((p) => p.best_model), ["gemini"]);
});

test("Zellwerte: Text mit = + - @ am Anfang wird nicht als Formel geschrieben", () => {
  const { cellValue } = require("./Code.gs");
  assert.equal(cellValue("- Check every loop"), "'- Check every loop");
  assert.equal(cellValue("=IMPORTXML(\"x\")"), "'=IMPORTXML(\"x\")");
  assert.equal(cellValue("+1"), "'+1");
  assert.equal(cellValue("@me"), "'@me");
  assert.equal(cellValue("You are careful"), "You are careful");
  assert.equal(cellValue(-0.5), -0.5);
  assert.equal(cellValue(true), true);
  assert.equal(cellValue(null), "");
  assert.equal(cellValue(undefined), "");
});

test("doppelt gesendete Läufe (gleiche run_id) zählen einmal", () => {
  const rows = [
    run({ run_id: "r1", model_key: "gemini", attitude: "strict", recall: 1 }),
    run({ run_id: "r1", model_key: "gemini", attitude: "strict", recall: 1 }),
    run({ run_id: "r2", model_key: "gemini", attitude: "strict", recall: 0 }),
  ];
  const data = aggregate(rows, DEFECTS, "live", false);
  assert.equal(data.runs, 2);
  assert.equal(data.recallHeatmap.gemini.strict, 0.5);
});

test("Einreichungen mit gleicher Nummer, aber verschiedener submission_id werden nicht addiert", () => {
  const sub = (id, tp) => run({ run_id: id + tp, group: "Gruppe 1", model_key: "gemini", phase: "a2_submit",
                                submission_no: 1, submission_id: id, tp, fp: 0, prompt_text: id });
  const { gallery, leaderboard } = aggregate([sub("s1", 1), sub("s2", 3)], DEFECTS, "live", false);
  assert.equal(gallery.length, 2);
  assert.deepEqual(leaderboard.map((e) => e.points), [6]);
});

test("Läufe mit Infrastrukturfehler (parse_ok leer) zählen nicht in die Wertung", () => {
  const rows = [
    run({ model_key: "kimi", attitude: "strict", recall: 1, parse_ok: true }),
    run({ model_key: "kimi", attitude: "strict", recall: "", tp: "", parse_ok: "", error: "401" }),
    run({ model_key: "kimi", attitude: "strict", recall: 0, parse_ok: false, error: "kein JSON" }),
  ];
  const data = aggregate(rows, DEFECTS, "live", false);
  assert.equal(data.recallHeatmap.kimi.strict, 0.5);
  assert.deepEqual(data.parseFailures.kimi, { failed: 1, total: 2 });
  assert.equal(data.infraErrors.kimi, 1);
});

test("join: Code ist groß/klein-unabhängig, Leerzeichen zählen nicht", () => {
  const { joinLookup } = require("./Code.gs");
  const keys = [{ code: "K7Q2", group: "Gruppe 2", openrouter_key: "sk-x", active: true }];
  assert.deepEqual(joinLookup(keys, { token: "t" }, { code: " k7 q2 ", token: "t" }),
                   { status: "ok", group: "Gruppe 2", key: "sk-x" });
});

test("join: ohne gültiges Token wird nichts herausgegeben", () => {
  const { joinLookup } = require("./Code.gs");
  const keys = [{ code: "K7Q2", group: "Gruppe 2", openrouter_key: "sk-x", active: "TRUE" }];
  [{ code: "K7Q2" }, { code: "K7Q2", token: "falsch" }, { code: "K7Q2", token: "" }].forEach((params) => {
    const answer = joinLookup(keys, { token: "t" }, params);
    assert.equal(answer.status, "error");
    assert.equal(JSON.stringify(answer).indexOf("sk-x"), -1);
  });
  // Auch ein leeres Token im Sheet öffnet nichts.
  assert.equal(joinLookup(keys, { token: "" }, { code: "K7Q2", token: "" }).status, "error");
});

test("join: unbekannte und inaktive Codes", () => {
  const { joinLookup } = require("./Code.gs");
  const keys = [{ code: "K7Q2", group: "Gruppe 2", openrouter_key: "sk-x", active: "FALSE" }];
  assert.deepEqual(joinLookup(keys, { token: "t" }, { code: "K7Q2", token: "t" }),
                   { status: "error", message: "Code unbekannt" });
  assert.equal(joinLookup(keys, { token: "t" }, { code: "", token: "t" }).status, "error");
});

test("menschliche Gutachten zählen nicht als LLM-Läufe", () => {
  const rows = [
    run({ phase: "human", model_key: "human", attitude: "strict", snippet_id: "bank_account", parse_ok: true, recall: 0.5 }),
    run({ phase: "human", model_key: "human", attitude: "none", snippet_id: "bank_account", parse_ok: "" }),
  ];
  const data = aggregate(rows, DEFECTS, "live", false);
  assert.deepEqual(data.models, []);
  assert.deepEqual(data.parseFailures, {});
  assert.deepEqual(data.infraErrors, {});
});

test("Phase setzen nur mit dem Admin-Token", () => {
  const { phaseUpdate } = require("./Code.gs");
  const config = { admin_token: "geheim" };
  assert.deepEqual(phaseUpdate(3, "geheim", config), { status: "ok", phase: 3 });
  assert.equal(phaseUpdate(3, "falsch", config).status, "error");
  assert.equal(phaseUpdate(3, "", config).status, "error");
  assert.equal(phaseUpdate(3, "", { admin_token: "" }).status, "error");
  assert.equal(phaseUpdate(3, undefined, {}).status, "error");
  assert.equal(phaseUpdate(6, "geheim", config).status, "error");
  assert.equal(phaseUpdate(-1, "geheim", config).status, "error");
  assert.equal(phaseUpdate("2", "geheim", config).phase, 2);
});

test("Phase lesen: fehlt oder unlesbar → 0", () => {
  const { readPhase } = require("./Code.gs");
  assert.equal(readPhase({ phase: "4" }), 4);
  assert.equal(readPhase({}), 0);
  assert.equal(readPhase({ phase: "x" }), 0);
});
