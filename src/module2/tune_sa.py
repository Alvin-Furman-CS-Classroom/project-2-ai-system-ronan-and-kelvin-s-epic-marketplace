"""
Simulated-annealing parameter tuning script.

Grid-searches over SA hyper-parameters (initial_temp, cooling_rate, min_temp)
using the working-set catalog and reports the best configuration by NDCG@k.

Usage:
    python -m src.module2.tune_sa

TODO (Ronan): Implement the grid search loop and result reporting.
"""

# TODO: import HeuristicRanker, ScoringConfig, load_catalog_from_working_set
# TODO: define parameter grid (initial_temp, cooling_rate, min_temp)
# TODO: run SA with each parameter combo on a representative SearchResult
# TODO: print best params + NDCG


def main() -> None:
    """Run SA parameter tuning."""
    raise NotImplementedError("Ronan: implement SA parameter tuning")


if __name__ == "__main__":
    main()
