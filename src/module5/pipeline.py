"""
End-to-end evaluation pipeline (Module 5).

Orchestrates Modules 1-4, computes evaluation metrics against a
held-out ground-truth set, and packages the final top-k payload.
Supports single-query evaluation and batch evaluation with
aggregated metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple

import numpy as np

from src.module1.catalog import Product, ProductCatalog
from src.module1.filters import SearchFilters
from src.module1.retrieval import CandidateRetrieval
from src.module2.ranker import HeuristicRanker
from src.module4.pipeline import LearningToRankPipeline
from src.module5.exceptions import EmptyCandidateError, EvaluationError
from src.module5.holdout import HeldOutSet
from src.module5.metrics import compute_all_metrics
from src.module5.payload import TopKResult, build_top_k_payload

if TYPE_CHECKING:
    from src.module3.embeddings import ProductEmbedder
    from src.module3.query_understanding import QueryResult, QueryUnderstanding

logger = logging.getLogger(__name__)


def _neutralise_query_result(qr: "QueryResult") -> "QueryResult":
    """Return a copy of *qr* with keywords dropped and embedding zeroed.

    Used for the ``use_query_understanding=False`` ablation when the trained
    LTR model is combined (13-dim): the model still needs a ``QueryResult``
    object to build features, but zeroing out the NLP signal gives a clean
    "quality-only at inference" ranking without needing to retrain.
    """
    from src.module3.query_understanding import QueryResult

    return QueryResult(
        keywords=[],
        query_embedding=np.zeros_like(qr.query_embedding),
        inferred_category=None,
        confidence=0.0,
        corrected_query=None,
    )


@dataclass(frozen=True)
class EvaluationResult:
    """Output of a single-query evaluation.

    Attributes:
        payload: The top-k user-facing result with product details.
        metrics: Evaluation metrics (precision, recall, F1, NDCG, MRR, AP).
        query: The query that was evaluated.
    """

    payload: TopKResult
    metrics: Dict[str, float]
    query: str


@dataclass(frozen=True)
class BatchEvaluationResult:
    """Output of a batch evaluation across multiple queries.

    Attributes:
        per_query: Individual evaluation results keyed by query.
        aggregate: Mean of each metric across all queries.
        num_queries: How many queries were evaluated.
    """

    per_query: Dict[str, EvaluationResult]
    aggregate: Dict[str, float]
    num_queries: int


class EvaluationPipeline:
    """Runs the full search pipeline and evaluates against held-out data.

    Wires together:
      - Module 1: ``CandidateRetrieval`` (filter-based candidate search)
      - Module 2: ``HeuristicRanker`` (heuristic re-ranking)
      - Module 3: ``QueryUnderstanding`` (NLP query parsing)
      - Module 4: ``LearningToRankPipeline`` (supervised re-ranking)
      - Module 5: metrics + payload assembly

    Args:
        catalog: Product catalog shared by all modules.
        retrieval: Module 1 retrieval engine.
        ranker: Module 2 heuristic ranker.
        ltr_pipeline: Module 4 learning-to-rank pipeline.
        query_understanding: Module 3 NLP orchestrator (optional).
        embedder: Module 3 product embedder (optional).
    """

    def __init__(
        self,
        catalog: ProductCatalog,
        retrieval: CandidateRetrieval,
        ranker: HeuristicRanker,
        ltr_pipeline: LearningToRankPipeline,
        query_understanding: Optional[QueryUnderstanding] = None,
        embedder: Optional[ProductEmbedder] = None,
    ) -> None:
        self._catalog = catalog
        self._retrieval = retrieval
        self._ranker = ranker
        self._ltr = ltr_pipeline
        self._qu = query_understanding
        self._embedder = embedder

    def evaluate(
        self,
        query: str,
        filters: SearchFilters,
        holdout: HeldOutSet,
        k: int = 10,
        ranking_strategy: str = "baseline",
        *,
        use_ltr: bool = True,
        use_query_understanding: bool = True,
    ) -> EvaluationResult:
        """Run the full pipeline for one query and compute metrics.

        Steps:
            1. Module 1 retrieval (filter candidates).
            2. Module 2 heuristic re-ranking.
            3. Module 3 query understanding (if available and enabled).
            4. Module 4 LTR scoring (if enabled).
            5. Build top-k payload.
            6. Compute metrics against held-out ground truth.

        Args:
            query: Free-text search query.
            filters: Hard constraints for Module 1.
            holdout: Ground-truth relevance data.
            k: Top-k cut-off for results and metrics.
            ranking_strategy: Module 2 strategy (baseline/hill_climbing/simulated_annealing).
            use_ltr: If False, keep Module 2 order only (ablation: no Module 4).
            use_query_understanding: If False, skip NLP features for LTR (ablation: quality-only
                inference when ``use_ltr`` is True).

        Returns:
            :class:`EvaluationResult` with payload and metrics.
        """
        search_result = self._retrieval.search(filters)

        if search_result.count == 0:
            empty_payload = build_top_k_payload([], self._catalog, query, k)
            return EvaluationResult(
                payload=empty_payload,
                metrics=compute_all_metrics([], set(), k),
                query=query,
            )

        ranked_result = self._ranker.rank(
            search_result, strategy=ranking_strategy, k=k,
        )
        candidate_products = [
            self._catalog[pid]
            for pid, _ in ranked_result.ranked_candidates
            if pid in self._catalog
        ]

        query_result: Optional[QueryResult] = None
        if self._qu is not None:
            query_result = self._qu.understand(query)

        # Module 3 text-rank pass: when QU is on, reorder candidates by
        # semantic + lexical relevance to the query (mirrors /api/search).
        module3_scores: Optional[Dict[str, float]] = None
        module3_ranked: Optional[List[Tuple[str, float]]] = None
        if (
            use_query_understanding
            and self._qu is not None
            and candidate_products
            and query.strip()
        ):
            texts = {
                p.id: f"{p.title} {p.description or ''}"
                for p in candidate_products
            }
            titles = {p.id: p.title for p in candidate_products}
            module3_ranked = self._qu.search_by_text(
                query, texts, top_k=len(candidate_products), titles=titles,
            )
            order = {pid: i for i, (pid, _) in enumerate(module3_ranked)}
            candidate_products.sort(key=lambda p: order.get(p.id, len(order)))
            module3_scores = {pid: score for pid, score in module3_ranked}

        if use_ltr:
            ltr_query_result = query_result
            if not use_query_understanding and query_result is not None:
                ltr_query_result = _neutralise_query_result(query_result)
            ltr_scored = self._ltr.rank(
                candidate_products,
                top_k=None,
                query_result=ltr_query_result,
                embedder=self._embedder,
                module3_scores=module3_scores,
            )
            # When Module 3 ran, blend its relevance into the LTR score —
            # same 0.55 / 0.45 mix the production /api/search route uses.
            if module3_scores:
                blended = [
                    (
                        pid,
                        0.55 * module3_scores.get(pid, 0.0) + 0.45 * score,
                    )
                    for pid, score in ltr_scored
                ]
                blended.sort(key=lambda x: x[1], reverse=True)
                final_scores = blended[:k]
            else:
                final_scores = ltr_scored[:k]
        elif module3_ranked is not None:
            final_scores = list(module3_ranked[:k])
        else:
            final_scores = list(ranked_result.ranked_candidates[:k])

        ranked_ids = [pid for pid, _ in final_scores]
        relevant_ids = holdout.get_relevant(query)

        metrics = compute_all_metrics(ranked_ids, relevant_ids, k)

        payload = build_top_k_payload(
            final_scores, self._catalog, query, k, metrics=metrics,
        )

        logger.info(
            "Evaluated query=%r  k=%d  P@k=%.3f  NDCG@k=%.3f  MRR=%.3f",
            query, k,
            metrics["precision_at_k"],
            metrics["ndcg_at_k"],
            metrics["reciprocal_rank"],
        )

        return EvaluationResult(payload=payload, metrics=metrics, query=query)

    def batch_evaluate(
        self,
        queries_and_filters: List[Tuple[str, SearchFilters]],
        holdout: HeldOutSet,
        k: int = 10,
        ranking_strategy: str = "baseline",
        *,
        use_ltr: bool = True,
        use_query_understanding: bool = True,
    ) -> BatchEvaluationResult:
        """Evaluate multiple queries and aggregate metrics.

        Args:
            queries_and_filters: List of ``(query_text, filters)`` pairs.
            holdout: Ground-truth relevance for all queries.
            k: Top-k cut-off.
            ranking_strategy: Module 2 strategy.
            use_ltr: If False, Module 2 order only (no Module 4).
            use_query_understanding: If False, skip query features for LTR when ``use_ltr``.

        Returns:
            :class:`BatchEvaluationResult` with per-query and aggregate metrics.
        """
        per_query: Dict[str, EvaluationResult] = {}

        for query, filters in queries_and_filters:
            result = self.evaluate(
                query, filters, holdout, k=k,
                ranking_strategy=ranking_strategy,
                use_ltr=use_ltr,
                use_query_understanding=use_query_understanding,
            )
            per_query[query] = result

        aggregate = self._aggregate_metrics(per_query)

        logger.info(
            "Batch evaluation: %d queries  mean P@k=%.3f  mean NDCG@k=%.3f  MAP=%.3f",
            len(per_query),
            aggregate.get("mean_precision_at_k", 0),
            aggregate.get("mean_ndcg_at_k", 0),
            aggregate.get("mean_average_precision", 0),
        )

        return BatchEvaluationResult(
            per_query=per_query,
            aggregate=aggregate,
            num_queries=len(per_query),
        )

    @staticmethod
    def _aggregate_metrics(
        per_query: Dict[str, EvaluationResult],
    ) -> Dict[str, float]:
        """Compute mean of each metric across queries."""
        if not per_query:
            return {}

        metric_keys = [
            "precision_at_k",
            "recall_at_k",
            "f1_at_k",
            "ndcg_at_k",
            "reciprocal_rank",
            "average_precision",
        ]

        aggregate: Dict[str, float] = {}
        for key in metric_keys:
            values = [r.metrics[key] for r in per_query.values() if key in r.metrics]
            if values:
                aggregate[f"mean_{key}"] = float(np.mean(values))

        return aggregate
