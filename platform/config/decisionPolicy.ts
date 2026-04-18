/**
 * Tunable decision-layer policy (no secrets). Adjust weights/thresholds without code changes in UI later.
 */
export const DECISION_POLICY = {
  /** Max items in the ranked decision queue returned to the client. */
  maxQueueItems: 40,
  /** Max SKU-level rows appended from overpriced/risk tags (before merge sort). */
  maxSkuDecisions: 15,
  /** Ignore SKU gaps below this SAR when building SKU decision lines (noise floor). */
  minSkuGapSar: 0.01,
  /** Scoring weights for queue ordering (relative). */
  scoreWeights: {
    /** Multiplier on 100 for alert ranking (keeps high alerts on top). */
    alertSeverity: { high: 0.92, medium: 0.78, low: 0.62 },
    recommendationPriorityPenalty: 2,
    recommendationImpactBonus: { high: 18, medium: 10, low: 4 },
    skuMaxScore: 88,
  },
  /** Scenario defaults (client can override). */
  scenarios: {
    matchCheapestDefaultTopN: 50,
    liftToMarketAvgDefaultTopN: 30,
    maxScenarioLineItems: 200,
  },
} as const

export type DecisionPolicy = typeof DECISION_POLICY
