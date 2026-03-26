"""
End-to-end learning-to-rank pipeline (Module 4).

Orchestrates feature extraction, optional training, and scoring to produce
``final_scores: List[Tuple[product_id, float]]`` for the top-k payload.

Depends on Module 2 (heuristic ranks / scores) and Module 3 (query features).
"""

# Implementation: LearningToRankPipeline or rank_with_ltr(...)
