// Statische Vorschau des Dashboards mit erfundenen Daten – Layout prüfen, ohne neu zu deployen.
//
//   node tools/dashboard_preview.mjs <Ausgabeordner>
//
// Schreibt view-1.html … view-5.html (je eine Ansicht, Admin-Modus an). Screenshot in 1280 × 720, z. B.:
//   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --window-size=1280,720 \
//     --screenshot=view-1.png file://$PWD/<Ausgabeordner>/view-1.html
// Der Seitentitel meldet „OVERFLOW“, wenn die Seite breiter als das Fenster ist (sonst „OK“); prüfbar mit --dump-dom.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const { aggregate, FIELDS, STRICT_VS_LENIENT } = require(join(root, "scoreboard", "Code.gs"));

const out = process.argv[2];
if (!out) {
  console.error("Aufruf: node tools/dashboard_preview.mjs <Ausgabeordner>");
  process.exit(2);
}

// Deterministischer Zufall, damit die Vorschau bei jedem Lauf gleich aussieht.
let seed = 7;
const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

const SNIPPETS = [["qb_bitcount", "L1", 1], ["qb_quicksort", "L2", 1], ["qb_levenshtein", "L3", 1],
                  ["qb_shunting_yard", "L4", 1], ["qb_next_permutation", "L5", 1], ["bank_account", "", 6]];
const START = { strict: 3.5, objective: 5.8, lenient: 7.2 };
const rows = [];
let id = 0;
const record = (o) => rows.push(Object.assign(Object.fromEntries(FIELDS.map((f) => [f, ""])),
  { session_id: "preview", run_id: "r" + id++, timestamp: String(id), parse_ok: true }, o));

[["Gruppe 1", "strict", 3, 2], ["Gruppe 2", "objective", 6, 3], ["Gruppe 3", "lenient", 8, 2], ["Gruppe 4", "none", 5, 4]]
  .forEach(([group, attitude, score, tp]) => record({ group, phase: "human", model_key: "human", attitude,
    snippet_id: "bank_account", weighted_score: score, tp, fp: 1, n_defects: 6, recall: tp / 6 }));

[["Gruppe 1", "gemini"], ["Gruppe 2", "deepseek"], ["Gruppe 3", "kimi"], ["Gruppe 4", "local"]].forEach(([group, model], g) => {
  const attitudes = model === "local" ? ["strict", "lenient"] : ["strict", "objective", "lenient"];
  SNIPPETS.forEach(([snippet, level, n]) => attitudes.forEach((attitude) => [false, true].forEach((withTests) => {
    if (model === "local" && withTests) return;
    const tp = Math.min(n, Math.round(rand() * n * (model === "local" ? 0.6 : 0.9) + 0.2));
    record({ group, phase: "a1", model_key: model, attitude, snippet_id: snippet, complexity_level: level,
             with_tests: withTests, weighted_score: Math.round((START[attitude] + rand() * 2 - 1) * 10) / 10,
             tp, fp: Math.round(rand() * (attitude === "strict" ? 3 : 1)), n_defects: n, recall: tp / n,
             found_defect_ids: tp ? "D1" : "", parse_ok: model === "local" ? rand() > 0.15 : true });
  })));
  record({ group, phase: "prognosis", prediction_best_model: ["gemini", "human", "kimi", "deepseek"][g],
           prediction_strict_vs_lenient: STRICT_VS_LENIENT[g % 3] });
  [1, 2].forEach((no) => SNIPPETS.forEach(([snippet]) => record({
    group, phase: "a2_submit", model_key: model, submission_no: no, submission_id: group + no, snippet_id: snippet,
    tp: Math.round(rand()), fp: Math.round(rand()), n_defects: 1,
    prompt_text: no === 2 ? "You are a meticulous reviewer.\n- Read the specification first.\n- Check every loop bound, " +
      "every comparison and every return value against it.\n- Report only defects you can justify." : "Be thorough." })));
});

const defects = SNIPPETS.flatMap(([snippet, , n]) => Array.from({ length: n }, (_, i) =>
  ({ snippet_id: snippet, defect_id: (snippet === "bank_account" ? "B" : "D") + (i + 1), kind: i < 3 ? "bug" : "quality",
     lines: String(10 + i * 5), description: "Beispielbeschreibung " + (i + 1) })));
const joins = [{ session_id: "preview", group: "Gruppe 1" }];
const payload = Object.assign(aggregate(rows, defects, "preview", false, joins), { phase: 3 });
payload.connected["Gruppe 4"] = false; // zeigt beide Zustände

const fake = `<script>
  window.google = { script: { run: (function () {
    const runner = { ok: null,
      withSuccessHandler(fn) { this.ok = fn; return this; },
      withFailureHandler() { return this; },
      getData() { const ok = this.ok; setTimeout(() => ok(${JSON.stringify(payload)}), 0); },
      setPhase(n) { const ok = this.ok; setTimeout(() => ok({ status: "ok", phase: n }), 0); } };
    return runner; })() } };
  window.addEventListener("load", () => setTimeout(() => {
    document.title = document.documentElement.scrollWidth > window.innerWidth ? "OVERFLOW" : "OK";
  }, 500));
</script>`;

const template = readFileSync(join(root, "scoreboard", "dashboard.html"), "utf8")
  .replace("<?= session ?>", JSON.stringify("preview"))
  .replace("<?= admin ?>", JSON.stringify("preview-admin"));
mkdirSync(out, { recursive: true });
[1, 2, 3, 4, 5].forEach((view) => {
  const page = template.replace("<script>\n    const SESSION", fake + `<script>window.INITIAL_VIEW = ${view};</script><script>\n    const SESSION`);
  writeFileSync(join(out, `view-${view}.html`), page);
});
console.log(`5 Ansichten in ${out}`);
