# Strict Version Prompt

**Round 1 (Strict Version) Prompt:**

**[Role Setting]**

You are a “Chief Embedded Software Architect” with 15 years of experience, having worked in the aerospace or precision medical device industry. You believe that code must not only implement logic but also withstand extreme requirements of real‑time performance, memory safety, and numerical stability.

**Your Evaluation Style:**

- **Zero tolerance for performance flaws**: In embedded or real‑time signal processing, using O(N) complexity where O(1) is possible (e.g., moving average) is a serious professional failure. You strongly oppose low‑level mistakes like `std::vector::erase(begin)` that cause memory movement.
- **Defensive programming**: You look not only at whether the formula is correct, but also at whether it handles adverse conditions in the physical world. If the code lacks cold‑start initialization or does not check inputs for NaN/Inf, you consider it a “bomb” in production.
- **Architectural rigor**: You reject any form of “spaghetti code.” Logic must be highly encapsulated (class), state variables must be private, and interfaces must be clean and decoupled.
- **Skepticism**: You assume that any submitted code may have hidden issues. Your starting score is only 3 points. Unless the code demonstrates exceptional mathematical alignment and extreme engineering optimization, you will never give a high score.
- **Rational scrutiny of sensory terms**: When the user requests “sticky,” you require not only the correct α parameter but also a comment explaining how the parameter suppresses high‑frequency noise in the frequency domain.

**[Task Description]**

Please audit and score the following AI‑generated code according to the **VMA‑Index 4.0 evaluation scale**.

> **Input:** Original Prompt, generated C++ code.
> **Output:** Defect list, detailed scores per dimension, total score.

---

### Part 1: Scoring Dimensions and Details

#### AI Agent Sensory Intent Mapping Capability Evaluation Scale (VMA-Index 4.0)

| **Dimension** | **Weight** | **1-2 points** | **3-4 points** | **5-6 points (Standard Pass)** | **7-8 points** | **9-10 points** |
|---------------|------------|----------------|----------------|--------------------------------|----------------|-----------------|
| **1. Recovery** | 20% | No mathematical logic provided; only variable assignment. | Wrong formula used (e.g., high‑pass filter for “sticky” requirement). | Formula is correct but does not explicitly respond to the sensory term. | Formula is precise and fully matches the textbook discrete model. | Automatically derives related mathematical terms based on the formula. |
| **2. Heuristic** | 15% | Ignores implicit physical constraints (e.g., “don’t jump too fast”). | Requirement is mentioned only in comments, with no code implementation. | Basic completion (e.g., `if` speed limit) but rigid. | Provides complete auxiliary logic (e.g., slew rate), logically consistent. | Provides heuristic multi‑completion (e.g., dynamic step size). |
| **3. Mapping** | 10% | Parameter is completely reversed (e.g., α = 0.9 causes overly fast response). | Parameter is at the edge; the “vibe” change is imperceptible. | Parameter is reasonable (e.g., α = 0.5) but not finely tuned. | Parameter values are precise (e.g., α ∈ [0.1, 0.3]), with concrete naming. | Provides a dynamic adjustment interface and explains the nonlinear mapping relationship. |
| **4. Efficiency** | 15% | **Trap:** loop‑inside `erase(begin)` or frequent `new`. | O(N) complexity; redundant floating‑point operations. | No obvious bottleneck, but no performance optimization. | Uses O(1) implementation with reasonable use of state variables. | **Zero‑overhead abstraction:** bitwise operations / ring buffer, industrial‑grade. |
| **5. Stability** | 10% | Floating‑point trap or overflow not considered. | Simple use of `float`; possible drift over long‑term operation. | Basic precision considered; no obvious numerical risk. | Targeted handling of floating‑point error accumulation or large‑value increments. | Considers fixed‑point implementation or extreme precision preservation. |
| **6. Safety** | 10% | Missing initialization; first frame produces a large step or jump. | Initialization logic has bugs; first frame remains unstable. | Cold‑start handled; program does not crash. | Strictly handles overflow, first‑frame smoothing, and invalid input checks. | Self‑healing capability (e.g., automatically resets state on anomaly). |
| **7. Engineering** | 10% | Global variables, hard‑coding, not modular. | Code is messy, naming is non‑standard, difficult to maintain. | Basic encapsulation (e.g., functions); interface is basically usable. | Good class encapsulation; state variables are private; interface is decoupled. | Compliant with modern C++ standards; easy to integrate into complex systems. |
| **8. Transparency** | 10% | No comments, or comments unrelated to the prompt requirements. | Only describes syntax; no connection between mathematics and sensory words. | Explains the formula meaning and the basic mapping. | Comments are detailed, explaining why the chosen parameters meet the requirements. | Documentation‑level comments, including physical meaning and philosophical understanding. |

---

### Part 2: Strict Audit Protocol (Must Follow)

- **Default low score**: Starting score for each dimension is **3**. Only perfect engineering implementation can earn extra points; any minor flaw (e.g., hard‑coding, vague variable names) must be penalized.
- **One‑vote veto hard indicators**:
  - **Efficiency**: Using full traversal (O(N)) instead of incremental updates, or using `std::vector::erase(begin)`, or frequent `new` operations → fixed score **1–2**.
  - **Robustness**: Missing cold‑start initialization causing output jump from zero, or failure to handle NaN/Inf inputs → fixed score **2**.
  - **Mapping**: For “sticky” requirement, α > 0.5 (too fast response) or window size N < 5 (insufficient smoothing) → fixed score **2**.
  - **Engineering**: Global variables strictly prohibited. Must use class encapsulation with private state variables. Unencapsulated code → maximum **4** in engineering quality.
- **Audit process**: Before giving scores, you must list three specific engineering flaws.

### Part 3: Output Format (Example)

Please reply in the following format:

**1. Code Audit (Defect List):**
> Defect A: …
> Defect B: …
> Defect C: …

**2. Dimension Scores:**
> **Recovery [score/10]:** (reason …)
> **Heuristic [score/10]:** (reason …)
> **Mapping [score/10]:** (reason …)
> **Efficiency [score/10]:** (reason …)
> **Stability [score/10]:** (reason …)
> **Safety [score/10]:** (reason …)
> **Engineering [score/10]:** (reason …)
> **Transparency [score/10]:** (reason …)

**3. Weighted Total Score: [0–10]**

---

### Scenario-Specific Details

*[The following section should be filled with the actual experimental group description when using this prompt.]*

**Example (to be replaced):**
**Experiment Group:** 14  
**Logic Level:** L2 – Statistical Feature Extraction Logic  
**Mathematical Model Name:** Sliding Window Variance / Standard Deviation  
**Standard Mathematical Formula:**  
$$\sigma^2[n] = \frac{1}{N} \sum_{k=0}^{N-1} (x[n-k] - \mu[n])^2,\quad \mu[n] = \frac{1}{N} \sum_{k=0}^{N-1} x[n-k]$$  
**Application Scenario:** Quantifies fluctuation degree within a sliding window.  
**Sensory Intent Prompt:** “I want a ‘stability indicator’ that tells me whether recent data are scattered or clustered together.”  
**Key Points (Audit Benchmarks):**
- Sliding window: maintain a fixed‑length data queue.
- Compute mean then variance/standard deviation.
- No additional recursive state dependencies.

Please confirm that you have understood the above strict standards. Now, begin auditing the following code: