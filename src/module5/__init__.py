# Module 5: Evaluation & Final Output
"""
Evaluation metrics and final output assembly for the Epic Marketplace.

**Topics:** Evaluation metrics for supervised learning

**Inputs:** final scores from Module 4, held-out interaction data
**Outputs:** top-k result payload with scores, plus evaluation metrics
    (Precision@k, Recall@k, NDCG@k, MRR, MAP)

**Success criterion:** Metrics are reported in a reproducible table and
    meet or exceed the Module 4 baseline.
"""

from .exceptions import (
    EmptyCandidateError,
    EvaluationError,
    HeldOutDataError,
    NoRelevantItemsError,
)
from .holdout import HeldOutSet, build_holdout_from_reviews, train_test_split_holdout
from .metrics import (
    average_precision,
    compute_all_metrics,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from .payload import TopKResult, build_top_k_payload
from .pipeline import (
    BatchEvaluationResult,
    EvaluationPipeline,
    EvaluationResult,
)

__all__ = [
    # Exceptions
    "EvaluationError",
    "NoRelevantItemsError",
    "EmptyCandidateError",
    "HeldOutDataError",
    # Metrics
    "precision_at_k",
    "recall_at_k",
    "ndcg_at_k",
    "reciprocal_rank",
    "average_precision",
    "compute_all_metrics",
    # Held-out data
    "HeldOutSet",
    "build_holdout_from_reviews",
    "train_test_split_holdout",
    # Payload
    "TopKResult",
    "build_top_k_payload",
    # Pipeline
    "EvaluationPipeline",
    "EvaluationResult",
    "BatchEvaluationResult",
]
