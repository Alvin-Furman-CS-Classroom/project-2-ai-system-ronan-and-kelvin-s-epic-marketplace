# Module 2: Heuristic Re-ranking
"""
Heuristic re-ranking using advanced search techniques.

Takes candidate IDs from Module 1 and re-orders them using a configurable
scoring function.  Supports three strategies:

- **baseline** — sort by weighted heuristic score (no optimisation).
- **hill_climbing** — iteratively swap adjacent items to maximise a
  ranking objective (steepest-ascent local search).
- **simulated_annealing** — probabilistic optimisation that accepts
  worse moves early to escape local optima, then converges.
"""

from .exceptions import EmptyCandidatesError, InvalidWeightsError, RankingError
from .ranker import HeuristicRanker, RankedResult
from .scorer import ScoringConfig, compute_score, normalize

__all__ = [
    # Core classes
    "HeuristicRanker",
    "RankedResult",
    "ScoringConfig",
    # Scoring helpers
    "compute_score",
    "normalize",
    # Exceptions
    "RankingError",
    "InvalidWeightsError",
    "EmptyCandidatesError",
]
