# Module 4: Learning-to-Rank
"""
Supervised learning-to-rank on top of Modules 1–3.

**Topics:** supervised learning (linear / logistic regression, evaluation basics)

**Inputs:** ranked candidates, product features, query features, training labels  
**Outputs:** final relevance scores per candidate

**Success criterion:** LTR improves NDCG@k over heuristic ranking on a held-out set.
"""

from .exceptions import (
    FeatureConstructionError,
    InsufficientTrainingDataError,
    LearningToRankError,
    ModelNotFittedError,
)
from .features import (
    FEATURE_DIM,
    FEATURE_NAMES,
    compute_quality_value_features,
)
from .model import QualityValueRanker
from .pipeline import LearningToRankPipeline

__all__ = [
    "LearningToRankError",
    "InsufficientTrainingDataError",
    "ModelNotFittedError",
    "FeatureConstructionError",
    "FEATURE_DIM",
    "FEATURE_NAMES",
    "compute_quality_value_features",
    "QualityValueRanker",
    "LearningToRankPipeline",
]
