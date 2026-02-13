# Code Review Skill

## Purpose

Review the current module against both the **Module Rubric** and the
**Code Elegance Rubric** before each checkpoint submission. Produce two
reports that the team can act on before pushing final code.

---

## When to Use

Run this skill **before every graded checkpoint**. The reviewer should:

1. Read the module spec in `README.md` (inputs, outputs, dependencies, tests).
2. Read all source files under the relevant `src/moduleN/` directory.
3. Read matching tests in `unit_tests/moduleN/` and `integration_tests/moduleN/`.
4. Score against both rubrics below.
5. Output the two reports described in the **Output** section.

---

## Rubric 1 — Module Review (50 pts)

### Part 1: Source Code Review (27 pts)

| Criterion | Max | What to Check |
|-----------|-----|---------------|
| **1.1 Functionality** | 8 | All features work. Edge cases handled. No crashes. |
| **1.2 Code Elegance & Quality** | 7 | Clean structure, good naming, appropriate abstraction. |
| **1.3 Documentation** | 4 | Docstrings on all public functions with param/return descriptions. Type hints used consistently. Complex logic has inline comments. |
| **1.4 I/O Clarity** | 3 | Inputs and outputs are crystal clear and easy to verify. |
| **1.5 Topic Engagement** | 5 | Deep engagement with the AI concept. Implementation reflects core concepts accurately. |

### Part 2: Testing Review (15 pts)

| Criterion | Max | What to Check |
|-----------|-----|---------------|
| **2.1 Test Coverage & Design** | 6 | Core functionality, edge cases, and error conditions covered. Clear unit vs integration distinction. |
| **2.2 Test Quality & Correctness** | 5 | All tests pass. Tests verify behaviour, not implementation. Test isolation maintained. |
| **2.3 Test Documentation & Organization** | 4 | Tests grouped logically. Clear, descriptive names. Docstrings where needed. |

### Part 3: GitHub Practices (8 pts)

| Criterion | Max | What to Check |
|-----------|-----|---------------|
| **3.1 Commit Quality & History** | 4 | Meaningful messages explaining *what* and *why*. Appropriately sized commits. |
| **3.2 Collaboration Practices** | 4 | Branches, PRs, code reviews, issues/project boards used. |

---

## Rubric 2 — Code Elegance (8 criteria, 0-4 each → averaged)

| # | Criterion | What to Check |
|---|-----------|---------------|
| 1 | **Naming Conventions** | Descriptive, PEP 8, intent-revealing names. |
| 2 | **Function & Method Design** | Concise, single-responsibility, ≤ ~25 lines typical. |
| 3 | **Abstraction & Modularity** | Well-judged classes/modules. No premature generalization. |
| 4 | **Style Consistency** | Uniform formatting. Would pass `ruff` with minimal warnings. |
| 5 | **Code Hygiene** | No dead code, no duplication, named constants. |
| 6 | **Control Flow Clarity** | Minimal nesting (≤ 3 levels). Early returns. Named conditions. |
| 7 | **Pythonic Idioms** | Comprehensions, context managers, `enumerate`, standard library. |
| 8 | **Error Handling** | Specific exceptions, caught at appropriate levels, useful messages. |

Average → Module Rubric mapping: 3.5-4.0 → 4 | 2.5-3.4 → 3 | 1.5-2.4 → 2 | 0.5-1.4 → 1 | <0.5 → 0

---

## Output

Generate **two files** per checkpoint:

### `checkpoint_X_elegance_report.md`

```
## Summary
1-2 sentences on overall quality.

## Findings
For each of the 8 criteria: score (0-4), brief justification, suggested fix (if any).

## Overall Score
Average across 8 criteria → module rubric equivalent.
```

### `checkpoint_X_module_report.md`

```
## Summary
1-2 sentences on module completeness and spec alignment.

## Findings
For each of the rubric criteria (1.1-1.5, 2.1-2.3, 3.1-3.2):
score, justification, gaps or suggestions.

## Total
Sum of all criteria out of 50.
```

---

## Module-Specific Checklists

### Module 1: Candidate Retrieval
- [ ] SearchFilters validates all inputs with custom exceptions
- [ ] ProductCatalog supports all required operations (add, get, iterate, index)
- [ ] CandidateRetrieval implements multiple search strategies (linear, BFS, DFS, priority)
- [ ] All strategies return correct and consistent candidate sets (100% recall)
- [ ] SearchResult provides typed output with metadata (strategy, elapsed_ms)
- [ ] Unit tests cover filters, catalog, retrieval, and edge cases
- [ ] Integration tests verify full pipeline end-to-end

### Module 2: Heuristic Re-ranking
- [ ] Scoring function is documented with clear formula
- [ ] Heuristic weights are configurable
- [ ] Integration test with Module 1 output

### Module 3: Query Understanding
- [ ] Keyword extraction is tested
- [ ] Embeddings have correct shape
- [ ] Category inference has baseline accuracy

### Module 4: Learning-to-Rank
- [ ] Model training is reproducible
- [ ] Feature extraction is documented
- [ ] NDCG improvement is measured

### Module 5: Evaluation & Output
- [ ] Metrics are correctly computed
- [ ] Output schema matches spec
- [ ] Results are reproducible

---

## Key References

- Module Rubric: https://csc-343.path.app/projects/project-2-ai-system/ai-system.rubric.md
- Code Elegance Rubric: https://csc-343.path.app/rubrics/code-elegance.rubric.md
- Checkpoint Guide: https://csc-343.path.app/projects/project-2-ai-system/checkpoint.guide.md
