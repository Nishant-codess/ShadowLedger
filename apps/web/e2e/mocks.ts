import { Page } from '@playwright/test';

export const mockBatchSummary = {
  batch_id: 'batch_20260905_demo',
  record_count: 1000,
  matched_count: 940,
  exception_count: 60,
  auto_resolved_count: 42,
  human_review_count: 15,
  unresolved_count: 3,
  match_rate: 0.94,
  enhanced_resolution_rate: 0.982,
  throughput_records_per_sec: 14250,
  total_volume_inr: 4500000,
  explained_volume_inr: 4485000,
  unexplained_volume_inr: 15000,
  processing_time_ms: 68,
  reason_code_breakdown: {
    EXACT_MATCH: 850,
    INVENTORY_SETTLEMENT: 25,
    FEE_BALANCED: 65,
    OFF_LEDGER_DEVIATION: 18,
  },
};

export const mockPatterns = [
  {
    cluster_id: 'pat_kirana_01',
    batch_id: 'batch_20260905_demo',
    case_ids: ['case_kirana_001', 'case_kirana_002'],
    pattern_signature: 'INVENTORY_SUBSTITUTION:CADBURY_DAIRY_MILK',
    exception_count: 24,
    total_value_at_risk: 240,
    likely_common_cause: 'Kirana small change coin shortage settled via Dairy Milk chocolate',
    evidence_strength: 0.95,
    created_at: '2026-09-05T12:00:00Z',
  },
  {
    cluster_id: 'pat_mobility_01',
    batch_id: 'batch_20260905_demo',
    case_ids: ['case_mobility_001'],
    pattern_signature: 'OFF_LEDGER_CASH_DEVIATION:AIRPORT_TOLL',
    exception_count: 12,
    total_value_at_risk: 1800,
    likely_common_cause: 'Driver collected unrecorded cash fare for airport toll bridge detour',
    evidence_strength: 0.88,
    created_at: '2026-09-05T12:00:00Z',
  },
];

export const mockCases = [
  {
    case_id: 'case_kirana_001',
    batch_id: 'batch_kirana_demo',
    observation_ids: ['obs_pos_01', 'obs_inv_01'],
    residual_amount: 10.0,
    financial_impact: 10.0,
    scenario_id: 'SCN_04',
    status: 'auto_resolve',
    pattern_cluster_id: 'pat_kirana_01',
    graph_json: {
      nodes: [
        { id: 'node_1', label: 'POS Bill ₹140', node_type: 'observation', amount: 140, confidence: 1.0, is_source_truth: true, event_type: 'payment', description: 'Cart Total' },
        { id: 'node_2', label: 'Bank UPI ₹130', node_type: 'observation', amount: 130, confidence: 1.0, is_source_truth: true, event_type: 'settlement', description: 'UPI Inward' },
        { id: 'node_3', label: 'Dairy Milk ₹10', node_type: 'latent_event', amount: 10, confidence: 0.94, is_source_truth: false, event_type: 'inventory_move', description: 'Barter Settlement' },
      ],
      links: [
        { source: 'node_1', target: 'node_2', amount: 130, value_type: 'money', direction: 'forward', confidence: 1.0 },
        { source: 'node_1', target: 'node_3', amount: 10, value_type: 'goods', direction: 'forward', confidence: 0.94 },
      ],
      node_count: 3,
      link_count: 2,
    },
    shadow_events: [
      {
        event_id: 'se_001',
        status: 'inferred',
        event_type: 'inventory_settlement',
        amount: 10.0,
        timestamp: '2026-09-05T12:00:00Z',
        confidence: 0.94,
        hypothesis_type: 'INVENTORY_SETTLEMENT',
      },
    ],
    decision: {
      decision: 'auto_resolve',
      reason_codes: ['INVENTORY_MATCH', 'HIGH_CONFIDENCE', 'MATERIALITY_OK'],
      evidence_confidence: 0.94,
      financial_materiality: 10.0,
      action_risk: 'low',
    },
    observations: [
      { observation_id: 'obs_pos_01', source_system: 'pos', event_type: 'payment', amount: 140.0, timestamp: '2026-09-05T12:00:00Z', description: 'Grocery Purchase' },
      { observation_id: 'obs_inv_01', source_system: 'inventory', event_type: 'inventory_move', amount: 10.0, timestamp: '2026-09-05T12:00:02Z', description: 'Cadbury Dairy Milk 10g SKU-CADB-10' },
    ],
  },
  {
    case_id: 'case_mobility_001',
    batch_id: 'batch_mobility_demo',
    observation_ids: ['obs_ride_01', 'obs_qr_01'],
    residual_amount: 150.0,
    financial_impact: 150.0,
    scenario_id: 'SCN_08',
    status: 'human_review',
    pattern_cluster_id: 'pat_mobility_01',
    graph_json: {
      nodes: [
        { id: 'node_ride', label: 'Ride Fare ₹350', node_type: 'observation', amount: 350, confidence: 1.0, is_source_truth: true, event_type: 'payment', description: 'Metered Fare' },
        { id: 'node_qr', label: 'Driver QR ₹500', node_type: 'observation', amount: 500, confidence: 0.9, is_source_truth: false, event_type: 'settlement', description: 'Personal QR scan' },
      ],
      links: [
        { source: 'node_ride', target: 'node_qr', amount: 150, value_type: 'money', direction: 'forward', confidence: 0.88 },
      ],
      node_count: 2,
      link_count: 1,
    },
    shadow_events: [
      {
        event_id: 'se_002',
        status: 'inferred',
        event_type: 'off_ledger_deviation',
        amount: 150.0,
        timestamp: '2026-09-05T12:05:00Z',
        confidence: 0.88,
        hypothesis_type: 'OFF_LEDGER_DEVIATION',
      },
    ],
    decision: {
      decision: 'human_review',
      reason_codes: ['OFF_LEDGER_SAFETY_GATE', 'MATERIALITY_CHECK'],
      evidence_confidence: 0.88,
      financial_materiality: 150.0,
      action_risk: 'medium',
    },
    observations: [
      { observation_id: 'obs_ride_01', source_system: 'ride_hailing', event_type: 'payment', amount: 350.0, timestamp: '2026-09-05T12:05:00Z', description: 'Airport Drop Trip' },
      { observation_id: 'obs_qr_01', source_system: 'external_trace', event_type: 'settlement', amount: 500.0, timestamp: '2026-09-05T12:06:00Z', description: 'Driver Personal UPI QR Code' },
    ],
  },
];

export const mockExplain = {
  case_id: 'case_kirana_001',
  headline: 'Reconstructed Barter Change Settlement',
  economic_story: 'The merchant gave the customer a Cadbury Dairy Milk worth ₹10 in lieu of physical cash coin change for a ₹140 POS cart paid with ₹130 bank settlement.',
  policy_action: 'Auto-resolve and debit Store Inventory asset account by ₹10.',
  narrative: 'Detailed audit reconstruction shows value conservation balanced across official bank ledger and latent inventory movement.',
  provider: 'Local Deterministic Synthesis (Qwen3 8B Fallback)',
  hypothesis_type: 'INVENTORY_SETTLEMENT',
  taxonomy_level: 'INFERRED_LATENT',
  evidence_confidence: 0.94,
  decision: 'auto_resolve',
  reason_codes: ['INVENTORY_MATCH', 'HIGH_CONFIDENCE'],
  total_payment: 140,
  total_settlement: 130,
  residual_amount: 10,
};

export const mockBenchmark = {
  batch_id: 'batch_benchmark_10k',
  records: 10000,
  baseline: {
    batch_id: 'batch_benchmark_10k',
    record_count: 10000,
    matched_count: 7200,
    exception_count: 2800,
    auto_resolved_count: 0,
    human_review_count: 0,
    unresolved_count: 2800,
    match_rate: 0.72,
    enhanced_resolution_rate: 0.72,
    throughput_records_per_sec: 18500,
    total_volume_inr: 25000000,
    explained_volume_inr: 18000000,
    unexplained_volume_inr: 7000000,
    processing_time_ms: 120,
    ground_truth_precision: 1.0,
    ground_truth_recall: 0.72,
    latent_hypothesis_accuracy: null,
    unsafe_resolutions_count: 0,
  },
  enhanced: {
    batch_id: 'batch_benchmark_10k',
    record_count: 10000,
    matched_count: 9850,
    exception_count: 150,
    auto_resolved_count: 2650,
    human_review_count: 120,
    unresolved_count: 30,
    match_rate: 0.985,
    enhanced_resolution_rate: 0.985,
    throughput_records_per_sec: 14200,
    total_volume_inr: 25000000,
    explained_volume_inr: 24880000,
    unexplained_volume_inr: 120000,
    processing_time_ms: 195,
    ground_truth_precision: 1.0,
    ground_truth_recall: 0.985,
    latent_hypothesis_accuracy: 0.992,
    unsafe_resolutions_count: 0,
    scenario_breakdown: {
      SCN_01: { total: 1200, exact_matches: 1200, auto_resolved: 1200, human_review: 0, unresolved: 0, correct_hypotheses: 1200 },
      SCN_04: { total: 800, exact_matches: 0, auto_resolved: 780, human_review: 20, unresolved: 0, correct_hypotheses: 780 },
      SCN_08: { total: 500, exact_matches: 0, auto_resolved: 0, human_review: 490, unresolved: 10, correct_hypotheses: 490 },
      SCN_12: { total: 300, exact_matches: 0, auto_resolved: 0, human_review: 0, unresolved: 300, correct_hypotheses: 300 },
    },
  },
  pattern_clusters: mockPatterns,
};

export const mockHeroDemo = {
  hero_id: 'hero_a',
  title: 'THE MISSING ₹2',
  description: 'A ₹100 purchase settled as ₹98 cash + ₹2 physical inventory change.',
  batch_summary: mockBatchSummary,
  cases: mockCases,
  pattern_clusters: mockPatterns,
};

export async function setupApiMocks(page: Page) {
  // Hero Demo endpoint
  await page.route('**/api/demo/hero/*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockHeroDemo),
    });
  });

  // Benchmark endpoint (must precede generic /api/metrics)
  await page.route('**/api/metrics/benchmark*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockBenchmark),
    });
  });

  // Metrics endpoint
  await page.route('**/api/metrics', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockBatchSummary),
    });
  });

  // Patterns endpoint
  await page.route('**/api/patterns*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockPatterns),
    });
  });

  // Cases list endpoint
  await page.route('**/api/cases', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockCases),
    });
  });

  // Explain endpoint for cases (both /api/cases/:id/explain and /api/explain/:id)
  await page.route(/\/api\/(?:cases\/[^/]+\/explain|explain\/[^/?]+)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockExplain),
    });
  });

  // Case action endpoint
  await page.route(/\/api\/cases\/([^/]+)\/action$/, async (route) => {
    const url = route.request().url();
    const caseId = url.split('/cases/')[1]?.split('/action')[0];
    const match = { ...(mockCases.find((c) => c.case_id === caseId) || mockCases[0]) };
    match.status = 'approved';
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(match),
    });
  });

  // Single case endpoint
  await page.route(/\/api\/cases\/([^/?]+)$/, async (route) => {
    const url = route.request().url();
    const caseId = url.split('/cases/')[1]?.split('?')[0];
    const match = mockCases.find((c) => c.case_id === caseId) || mockCases[0];
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(match),
    });
  });

  // Explain endpoint
  await page.route(/\/api\/explain\/([^/?]+)$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockExplain),
    });
  });

  // Batch process endpoint
  await page.route('**/api/batches/process', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockBatchSummary),
    });
  });

  // Hero Demo endpoint
  await page.route(/\/api\/demo\/hero\/([^/?]+)$/, async (route) => {
    const url = route.request().url();
    const heroId = url.split('/hero/')[1]?.split('?')[0] || 'hero_a';
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        hero_id: heroId,
        title: 'Kirana Barter Inventory Settlement',
        description: 'Auto-resolved ₹10 residual via inventory deduction',
        batch_summary: mockBatchSummary,
        cases: mockCases,
        pattern_clusters: mockPatterns,
      }),
    });
  });

  // Health check endpoint
  await page.route('**/health', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'healthy',
        version: '0.1.0',
        engine: 'DuckDB+Polars',
        database: 'connected',
      }),
    });
  });
}
