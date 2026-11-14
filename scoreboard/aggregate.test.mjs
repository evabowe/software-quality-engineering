// Tests für die Aggregation des Scoreboards: node --test scoreboard/aggregate.test.mjs (läuft auch über pytest)
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { aggregate, cellValue, joinLookup, rowValues, FIELDS } = require("./Code.gs");

const KEYS = [
  { code: "AAAA", group: "Gruppe 1", openrouter_key: "sk-1", active: true },
  { code: "BBBB", group: "Gruppe 2", openrouter_key: "sk-2", active: "TRUE" },
  { code: "CCCC", group: "Gruppe 3", openrouter_key: "sk-3", active: true },
  { code: "DDDD", group: "Gruppe 4", openrouter_key: "sk-4", active: true },
  { code: "EEEE", group: "Gruppe alt", openrouter_key: "sk-5", active: "FALSE" },
];
let counter = 0;

function row(overrides) {
  counter += 1;
  const base = Object.fromEntries(FIELDS.map((f) => [f, ""]));
  return Object.assign(base, {
    timestamp: "2026-11-14T10:00:00+00:00", run_id: "r" + counter, session_id: "live", gruppe: "Gruppe 1",
    runde: 1, snippet: "bank_account", modell: "openai/gpt-6-luna", prompt: "p", code_score: 5, judge_score: 1,
    einreichung: "e" + counter,
  }, overrides);
}

function curve(gruppe, einreichung, timestamp, overrides) {
  const names = ["qb_bitcount", "qb_quicksort", "qb_levenshtein", "qb_shunting_yard", "qb_next_permutation"];
  return names.map((snippet, i) => row(Object.assign({ gruppe, einreichung, timestamp, snippet,
    komplexitaet: "L" + (i + 1), code_score: 10 - i, judge_score: i }, overrides ? overrides(i) : {})));
}

test("FIELDS endet mit session_id", () => {
  assert.equal(FIELDS[FIELDS.length - 1], "session_id");
});

test("Kopfzeile: leer oder genau FIELDS passt, alte 34-Spalten-Kopfzeile nicht", () => {
  const { headerMatches } = require("./Code.gs");
  assert.equal(headerMatches([]), true);
  assert.equal(headerMatches([""]), true);
  assert.equal(headerMatches(FIELDS.slice()), true);
  assert.equal(headerMatches(["timestamp", "run_id", "session_id", "group", "phase"]), false);
});

test("Runde 2 zeigt die neueste Zeile je Gruppe", () => {
  const rows = [
    row({ runde: 2, prompt: "alt", timestamp: "2026-11-14T10:00:00+00:00" }),
    row({ runde: 2, prompt: "neu", code_score: "6.5", judge_score: "3", timestamp: "2026-11-14T10:05:00+00:00" }),
    row({ runde: 1, prompt: "andere Runde", timestamp: "2026-11-14T10:09:00+00:00" }),
  ];
  const tile = aggregate(rows, KEYS, [], "live").rounds["2"]["Gruppe 1"];
  assert.deepEqual(tile, { judge_score: 3, code_score: 6.5, prompt: "neu", snippet: "bank_account",
                           modell: "openai/gpt-6-luna", timestamp: "2026-11-14T10:05:00.000Z" });
});

test("Zeitstempel als Date-Objekt (so liefert Sheets sie oft) werden verglichen", () => {
  const rows = [
    row({ runde: 1, prompt: "neu", timestamp: new Date("2026-11-14T10:05:00Z") }),
    row({ runde: 1, prompt: "alt", timestamp: "2026-11-14T10:00:00+00:00" }),
  ];
  assert.equal(aggregate(rows, KEYS, [], "live").rounds["1"]["Gruppe 1"].prompt, "neu");
});

test("doppelte run_id zählt einmal", () => {
  const rows = curve("Gruppe 1", "x", "2026-11-14T10:00:00+00:00", () => ({ runde: 4 }));
  rows.push(Object.assign({}, rows[0]));
  const total = aggregate(rows, KEYS, [], "live").rounds["4"]["Gruppe 1"];
  assert.equal(total.n, 5);
  assert.equal(total.judge_score, 0 + 1 + 2 + 3 + 4);
});

test("dieselbe Einreichung zweimal gesendet (neue run_ids) zählt in Runde 3 und 4 einmal", () => {
  const once = curve("Gruppe 1", "x", "2026-11-14T10:00:00+00:00", () => ({ runde: 4 }));
  const again = curve("Gruppe 1", "x", "2026-11-14T10:01:00+00:00", () => ({ runde: 4 }));
  const data = aggregate(once.concat(again), KEYS, [], "live");
  assert.equal(data.rounds["4"]["Gruppe 1"].n, 5);
  assert.equal(data.rounds["4"]["Gruppe 1"].judge_score, 10);
  const r3 = curve("Gruppe 2", "y", "2026-11-14T10:00:00+00:00", () => ({ runde: 3 }))
    .concat(curve("Gruppe 2", "y", "2026-11-14T10:01:00+00:00", () => ({ runde: 3 })));
  assert.equal(aggregate(r3, KEYS, [], "live").rounds["3"]["Gruppe 2"].points.length, 5);
});

test("rowValues: Zahlenfelder als Zahl, alle anderen Texte als Text (kein Datum, keine Formel)", () => {
  const record = { timestamp: "2026-11-14T10:00:00+00:00", run_id: "abc", gruppe: "Gruppe 1", runde: "4",
                   snippet: "qb_bitcount", komplexitaet: "L1", modell: "m", prompt: "TRUE", code_score: "5.2",
                   judge_score: "-1", einreichung: "1/2" };
  const values = rowValues(record, "live");
  const at = (f) => values[FIELDS.indexOf(f)];
  assert.equal(values.length, FIELDS.length);
  assert.equal(at("runde"), 4);
  assert.equal(at("code_score"), 5.2);
  assert.equal(at("judge_score"), -1);
  assert.equal(at("timestamp"), "'2026-11-14T10:00:00+00:00");
  assert.equal(at("prompt"), "'TRUE");
  assert.equal(at("einreichung"), "'1/2");
  assert.equal(at("session_id"), "'live");
  assert.equal(rowValues({ code_score: "" }, "live")[FIELDS.indexOf("code_score")], "");
  assert.equal(rowValues({}, "live")[FIELDS.indexOf("prompt")], "");
});

test("andere session_id wird ignoriert", () => {
  const rows = [row({ session_id: "probe" })];
  assert.equal(aggregate(rows, KEYS, [], "live").rounds["1"]["Gruppe 1"], null);
});

test("Runde 3 nimmt nur die neueste Einreichung, sortiert L1–L5", () => {
  const older = curve("Gruppe 2", "alt", "2026-11-14T10:00:00+00:00", () => ({ runde: 3, prompt: "alt" }));
  const newer = curve("Gruppe 2", "neu", "2026-11-14T10:10:00+00:00", () => ({ runde: 3, prompt: "neu" })).reverse();
  const c = aggregate(older.concat(newer), KEYS, [], "live").rounds["3"]["Gruppe 2"];
  assert.equal(c.prompt, "neu");
  assert.deepEqual(c.points.map((p) => p.komplexitaet), ["L1", "L2", "L3", "L4", "L5"]);
  assert.deepEqual(c.points[0], { komplexitaet: "L1", snippet: "qb_bitcount", code_score: 10, judge_score: 0 });
});

test("Runde 4 summiert judge_score, mittelt code_score und ignoriert leere Werte", () => {
  const judge = [2, 3, 1, "", 0];
  const code = [8, 6, "", 4, 2];
  const rows = curve("Gruppe 3", "e", "2026-11-14T10:00:00+00:00", (i) => ({ runde: 4, judge_score: judge[i],
                                                                            code_score: code[i] }));
  const total = aggregate(rows, KEYS, [], "live").rounds["4"]["Gruppe 3"];
  assert.deepEqual(total, { judge_score: 6, code_score: 5, n: 5, prompt: "p", modell: "openai/gpt-6-luna",
                            timestamp: "2026-11-14T10:00:00.000Z" });
});

test("leaders enthält bei Gleichstand beide Gruppen", () => {
  const rows = curve("Gruppe 1", "a", "2026-11-14T10:00:00+00:00", () => ({ runde: 4 }))
    .concat(curve("Gruppe 2", "b", "2026-11-14T10:00:00+00:00", () => ({ runde: 4 })))
    .concat(curve("Gruppe 3", "c", "2026-11-14T10:00:00+00:00", () => ({ runde: 4, judge_score: 0 })));
  assert.deepEqual(aggregate(rows, KEYS, [], "live").leaders, ["Gruppe 1", "Gruppe 2"]);
});

test("leaders ist leer ohne Daten in Runde 4", () => {
  assert.deepEqual(aggregate([row({ runde: 1 })], KEYS, [], "live").leaders, []);
});

test("Gruppen aus keys zuerst, inaktive nicht, fremde aus rows hinten", () => {
  const rows = [row({ gruppe: "Team Rot" }), row({ gruppe: "Gruppe 2" }), row({ gruppe: "Team Rot", session_id: "x" })];
  const data = aggregate(rows, KEYS, [], "live");
  assert.deepEqual(data.groups, ["Gruppe 1", "Gruppe 2", "Gruppe 3", "Gruppe 4", "Team Rot"]);
  assert.equal(data.rounds["1"]["Team Rot"].prompt, "p");
});

test("connected nur für Joins der aktiven Session", () => {
  const joins = [{ timestamp: "t", session_id: "live", group: "Gruppe 2" },
                 { timestamp: "t", session_id: "probe", group: "Gruppe 3" }];
  const data = aggregate([], KEYS, joins, "live");
  assert.equal(data.connected["Gruppe 2"], true);
  assert.equal(data.connected["Gruppe 3"], false);
});

test("ohne Daten: alle Kacheln null", () => {
  const data = aggregate([], KEYS, [], "live");
  assert.equal(data.session, "live");
  ["1", "2", "3", "4"].forEach((r) => data.groups.forEach((g) => assert.equal(data.rounds[r][g], null)));
});

test("Zellwerte: Text mit = + - @ am Anfang wird nicht als Formel geschrieben", () => {
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

test("join: Code ist groß/klein-unabhängig, Leerzeichen zählen nicht", () => {
  const keys = [{ code: "K7Q2", group: "Gruppe 2", openrouter_key: "sk-x", active: true }];
  assert.deepEqual(joinLookup(keys, { token: "t" }, { code: " k7 q2 ", token: "t" }),
                   { status: "ok", group: "Gruppe 2", key: "sk-x" });
});

test("join: ohne gültiges Token wird nichts herausgegeben", () => {
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
  const keys = [{ code: "K7Q2", group: "Gruppe 2", openrouter_key: "sk-x", active: "FALSE" }];
  assert.deepEqual(joinLookup(keys, { token: "t" }, { code: "K7Q2", token: "t" }),
                   { status: "error", message: "Code unbekannt" });
  assert.equal(joinLookup(keys, { token: "t" }, { code: "", token: "t" }).status, "error");
});
