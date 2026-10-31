## Output format

Respond only with a single JSON object that follows this schema, without Markdown fences and without any text before or after it:

{
  "findings": [
    {
      "line_start": 7,
      "line_end": 7,
      "category": "bug | robustness | maintainability | style",
      "severity": "high | medium | low",
      "description": "what is wrong and why",
      "suggested_fix": "corrected code line(s)"
    }
  ],
  "scores": {"functional_correctness": 0, "reliability": 0, "maintainability": 0, "readability": 0},
  "overall_score": 0.0
}

Rules:
- "line_start" and "line_end" refer to the line numbers shown on the left of the code.
- "category" is exactly one of "bug", "robustness", "maintainability", "style".
- "severity" is exactly one of "high", "medium", "low".
- Every score is a number from 0 to 10.
- If you find no defects, return an empty "findings" list.
