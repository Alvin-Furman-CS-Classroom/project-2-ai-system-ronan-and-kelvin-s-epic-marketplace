# Code Review Skill

## Purpose

Review code against the project rubric to identify gaps before checkpoint submission.

## Rubric Criteria

Based on the [Code Elegance Rubric](https://csc-343.path.app/rubrics/code-elegance.rubric.md):

### 1. Clarity & Readability
- [ ] Code is well-organized with clear naming conventions
- [ ] Functions/methods have docstrings explaining purpose, args, and returns
- [ ] Complex logic has inline comments
- [ ] Consistent formatting throughout

### 2. Modularity
- [ ] Single responsibility principle: each function does one thing
- [ ] Code is organized into logical modules/files
- [ ] No duplicate code (DRY principle)
- [ ] Clear separation between data, logic, and I/O

### 3. Correctness
- [ ] All unit tests pass
- [ ] Integration tests pass (where applicable)
- [ ] Edge cases are handled
- [ ] Input validation is present

### 4. Efficiency
- [ ] Appropriate data structures used
- [ ] No unnecessary loops or computations
- [ ] Time/space complexity is reasonable for the problem

### 5. Testability
- [ ] Unit tests exist for each module
- [ ] Tests cover happy path and edge cases
- [ ] Test fixtures are reusable
- [ ] Integration tests demonstrate module interactions

## How to Use This Skill

1. Run this skill after implementing a module
2. Check each criterion against the code
3. List any gaps found
4. Fix gaps before checkpoint submission

## Review Checklist by Module

### Module 1: Candidate Retrieval
- [ ] SearchFilters validates inputs
- [ ] ProductCatalog supports all required operations
- [ ] CandidateRetrieval implements multiple search strategies
- [ ] All strategies return correct results (100% recall for matches)
- [ ] Unit tests cover filters, catalog, and retrieval

### Module 2: Heuristic Re-ranking
- [ ] Scoring function is documented
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
