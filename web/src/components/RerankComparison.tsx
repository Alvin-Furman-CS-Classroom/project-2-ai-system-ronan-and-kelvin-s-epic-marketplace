/**
 * RerankComparison — Side-by-side comparison of Module 1 vs Module 2 results.
 *
 * Displays raw search results (Module 1) alongside re-ranked results (Module 2)
 * so users can see how heuristic re-ranking changes the ordering.
 *
 * Features:
 * - Strategy dropdown (baseline, hill_climbing, simulated_annealing)
 * - Side-by-side product cards with rank change indicators
 * - NDCG score and iteration count display
 *
 * TODO (Ronan): Implement the component.
 */

import React from "react";

export default function RerankComparison() {
  // TODO: state for strategy selection
  // TODO: fetch /api/search and /api/rerank with same filters
  // TODO: display side-by-side results with rank changes
  // TODO: show metadata (NDCG, iterations, elapsed time)

  return (
    <div>
      <h2>Re-rank Comparison</h2>
      <p>TODO: Implement side-by-side Module 1 vs Module 2 comparison</p>
    </div>
  );
}
