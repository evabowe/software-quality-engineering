// Statische Vorschau des Dashboards mit erfundenen Daten – Layout prüfen, ohne neu zu deployen.
//
//   node tools/dashboard_preview.mjs <Ausgabeordner>
//
// Schreibt runde-1.html … runde-4.html und öffnet sie im Browser (Doppelklick genügt). Screenshot in 1280 × 720, z. B.:
//   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --window-size=1280,720 \
//     --virtual-time-budget=3000 --screenshot=runde-1.png file://$PWD/<Ausgabeordner>/runde-1.html
// Der Seitentitel meldet „OVERFLOW“, wenn die Seite breiter als das Fenster ist (sonst „OK“); prüfbar mit --dump-dom.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const { aggregate, FIELDS } = require(join(root, "scoreboard", "Code.gs"));

const out = process.argv[2];
if (!out) {
  console.error("Aufruf: node tools/dashboard_preview.mjs <Ausgabeordner>");
  process.exit(1);
}

const SNIPPETS = [["qb_bitcount", "L1"], ["qb_quicksort", "L2"], ["qb_levenshtein", "L3"],
                  ["qb_shunting_yard", "L4"], ["qb_next_permutation", "L5"]];
const PROMPTS = {
  "Gruppe 1": "Du bist ein strenger Senior-Reviewer. Prüfe jede Zeile auf Randfälle,\n- jede Schleifengrenze\n- " +
              "jeden Rückgabewert\ngegen die Spezifikation und melde nur Fehler, die du begründen kannst.",
  "Gruppe 2": "Du bist ein wohlwollender Mentor für Studierende im 2. Semester.",
  "Gruppe 3": "Bewerte objektiv nach ISO 25010.",
};
const MODELS = { "Gruppe 1": "openai/gpt-6-luna", "Gruppe 2": "openai/gpt-6-luna", "Gruppe 3": "openai/gpt-6-sol" };
const now = Date.now();
let id = 0;
const rows = [];

function add(gruppe, runde, snippet, komplexitaet, code, judge, einreichung, minutesAgo) {
  id += 1;
  const r = Object.fromEntries(FIELDS.map((f) => [f, ""]));
  rows.push(Object.assign(r, {
    timestamp: new Date(now - minutesAgo * 60000).toISOString(), run_id: "r" + id, session_id: "preview",
    gruppe, runde, snippet, komplexitaet, modell: MODELS[gruppe], prompt: PROMPTS[gruppe],
    code_score: code, judge_score: judge, einreichung,
  }));
}

// Gruppe 4 hat noch nichts gesendet (in Runde 1 nur verbunden).
Object.keys(PROMPTS).forEach((g, gi) => {
  add(g, 1, "bank_account", "", 6.2 - gi, 2 + gi, g + "-1", 3 + gi);
  add(g, 2, "bank_account", "", [3.8, 6.9, 5.2][gi], [7, 4, 5][gi], g + "-2", 2 + gi);
  SNIPPETS.forEach(([s, level], i) => add(g, 3, s, level, 8.5 - i * (1 + gi * 0.3), [2, 1, 2][gi] - i % 3 + gi,
                                          g + "-3", 1 + gi));
  SNIPPETS.forEach(([s, level], i) => {
    if (gi === 2 && i === 2) return; // ein fehlgeschlagenes Snippet → 4/5
    add(g, 4, s, level, 7 - i * 0.5, [3, 2, 3][gi] - (i % 2), g + "-4", 1);
  });
});

const keys = ["Gruppe 1", "Gruppe 2", "Gruppe 3", "Gruppe 4"].map((group, i) =>
  ({ code: "C" + i, group, openrouter_key: "sk-x", active: true }));
const joins = [{ session_id: "preview", group: "Gruppe 4" }];
const payload = aggregate(rows, keys, joins, "preview");

const fake = `<script>
  window.google = { script: { run: {
    ok: null,
    withSuccessHandler(fn) { this.ok = fn; return this; },
    withFailureHandler() { return this; },
    getData() { const ok = this.ok; setTimeout(() => ok(${JSON.stringify(payload)}), 0); },
  } } };
  window.addEventListener("load", () => setTimeout(() => {
    document.title = document.documentElement.scrollWidth > window.innerWidth ? "OVERFLOW" : "OK";
  }, 500));
</script>`;

const template = readFileSync(join(root, "scoreboard", "dashboard.html"), "utf8");
mkdirSync(out, { recursive: true });
[1, 2, 3, 4].forEach((n) => {
  const page = template.replace("<script>\n    const REFRESH_MS",
                                fake + `<script>window.INITIAL_VIEW = ${n};</script><script>\n    const REFRESH_MS`);
  writeFileSync(join(out, `runde-${n}.html`), page);
});
console.log(`4 Runden in ${out}`);
