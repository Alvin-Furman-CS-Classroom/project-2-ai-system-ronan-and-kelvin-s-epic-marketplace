## Project Context

- System title: Epic Marketplace
- Theme: Small business marketplace search with search, NLP, and supervised ranking
- Proposal link or summary: See `PROPOSAL.md`

**Module plan:**

| Module | Topic(s) | Inputs | Outputs | Depends On | Checkpoint |
| ------ | -------- | ------ | ------- | ---------- | ---------- |
| 1: Candidate Retrieval | Uninformed/Informed Search | Filters, catalog | Candidate IDs | Search unit | Checkpoint 1 — Feb 11 |
| 2: Heuristic Re-ranking | Advanced Search | Candidate IDs, product/query features | Ranked candidates | Module 1 | Checkpoint 2 — Feb 26 |
| 3: Query Understanding | NLP before LLMs | Query text | Keywords, embedding, inferred category | Module 1 | Checkpoint 3 — Mar 19 |
| 4: Learning-to-Rank | Supervised Learning | Ranked candidates, features, labels | Final scores | Modules 2-3 | Checkpoint 4 — Apr 2 |
| 5: Evaluation & Output | Evaluation Metrics | Final scores, held-out data | Top-k payload, metrics | Module 4 | Checkpoint 5 — Apr 16 |
| 6 (optional) |  |  |  |  |  |

## Constraints

- 5-6 modules total, each tied to course topics.
- Each module must have clear inputs/outputs and tests.
- Align module timing with the course schedule.

## How the Agent Should Help

- Draft plans for each module before coding.
- Suggest clean architecture and module boundaries.
- Identify missing tests and edge cases.
- Review work against the rubric using the code-review skill.

## Agent Workflow

1. Ask for the current module spec from `README.md`.
2. Produce a plan (use "Plan" mode if available).
3. Wait for approval before writing or editing code.
4. After implementation, run the code-review skill and list gaps.

## Key References

- Project Instructions: https://csc-343.path.app/projects/project-2-ai-system/ai-system.project.md
- Code elegance rubric: https://csc-343.path.app/rubrics/code-elegance.rubric.md
- Course schedule: https://csc-343.path.app/resources/course.schedule.md
- Rubric: https://csc-343.path.app/projects/project-2-ai-system/ai-system.rubric.md
