## Evaluation scale (based on ISO/IEC 25010)

Score each of the four dimensions from 0 to 10.

| Dimension | Weight | Key question |
|---|---|---|
| functional_correctness | 40% | Does the code fulfil its specification for every input the specification allows? |
| reliability | 20% | Does it handle edge cases and invalid input, report errors clearly, and always terminate? |
| maintainability | 25% | Is it free of dead code, unreachable statements, unused parameters, and needless complexity? |
| readability | 15% | Are names, structure, and comments clear? |

Anchors for every dimension:

| Score | functional_correctness | reliability | maintainability | readability |
|---|---|---|---|---|
| 1–2 | Wrong for typical inputs | May hang or crash on typical inputs | Large parts are dead, duplicated, or tangled | Very hard to follow |
| 3–4 | Wrong for important cases | Crashes or misbehaves on common edge cases | Several dead or misleading parts | Misleading names or structure |
| 5–6 | Correct for typical inputs, wrong for some edge cases | Basic edge cases handled | Some dead code or unused parameters | Understandable with effort |
| 7–8 | Correct for all specified inputs, minor doubts | Edge cases and invalid input handled | Clean, minor issues | Clear names and structure |
| 9–10 | Demonstrably correct for all specified inputs | All edge cases handled with clear errors | No dead code, minimal and well structured | Self-explanatory, well documented |
