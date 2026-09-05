/** Typed API Client for ShadowLedger Backend */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PatternCluster {
  cluster_id: string;
  batch_id: string;
  case_ids: string[];
  pattern_signature: string;
  exception_count: number;
  total_value_at_risk: number;
  likely_common_cause: string;
  evidence_strength: number;
  created_at?: string;
}

export interface BatchSummary {
  batch_id: string;
  record_count: number;
  matched_count: number;
  exception_count: number;
  auto_resolved_count?: number;
  human_review_count?: number;
  unresolved_count?: number;
  match_rate: number;
  enhanced_resolution_rate?: number;
  throughput_records_per_sec: number;
  total_volume_inr: number;
  explained_volume_inr: number;
  unexplained_volume_inr: number;
  processing_time_ms: number;
  reason_code_breakdown?: Record<string, number>;
  pattern_clusters?: PatternCluster[];
}

export interface CaseDetail {
  case_id: string;
  batch_id: string;
  observation_ids: string[];
  residual_amount: number;
  financial_impact: number;
  scenario_id?: string;
  status: string;
  pattern_cluster_id?: string;
  graph_json?: {
    nodes: Array<{
      id: string;
      label: string;
      node_type: string;
      amount: number;
      confidence: number;
      is_source_truth: boolean;
      source_system?: string;
      event_type?: string;
      description?: string;
      timestamp?: string;
      [key: string]: unknown;
    }>;
    links: Array<{
      source: string;
      target: string;
      amount: number;
      value_type: string;
      direction: string;
      confidence: number;
      [key: string]: unknown;
    }>;
    node_count: number;
    link_count: number;
  };
  shadow_events?: Array<{
    event_id: string;
    status: string;
    event_type: string;
    amount: number;
    timestamp: string;
    confidence?: number;
    hypothesis_type?: string;
  }>;
  decision?: {
    decision: string;
    reason_codes: string[];
    evidence_confidence: number;
    financial_materiality: number;
    action_risk: string;
  };
  observations?: Array<{
    observation_id: string;
    source_system: string;
    event_type: string;
    amount: number;
    timestamp: string;
    description: string;
    entity_ids?: Record<string, string>;
  }>;
}

export interface HeroDemoResponse {
  hero_id: string;
  title: string;
  description: string;
  batch_summary: BatchSummary;
  cases: CaseDetail[];
  pattern_clusters: PatternCluster[];
}

export interface AIExplainResponse {
  case_id: string;
  headline: string;
  economic_story: string;
  policy_action: string;
  narrative: string;
  simple_narrative?: string;
  auditor_narrative?: string;
  deterministic_narrative?: string;
  provider: string;
  hypothesis_type: string;
  taxonomy_level: string;
  evidence_confidence: number;
  decision: string;
  reason_codes: string[];
  total_payment: number;
  total_settlement: number;
  residual_amount: number;
}

export interface HealthStatus {
  status: string;
  version: string;
  engine: string;
  database: string;
}

export async function fetchHealth(): Promise<HealthStatus | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function processBatch(rows: number = 100, seed: number = 42): Promise<BatchSummary | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/batches/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows, seed }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function triggerHeroDemo(heroId: string): Promise<HeroDemoResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/demo/hero/${heroId}`, {
      method: "POST",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchLatestMetrics(): Promise<BatchSummary | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/metrics`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchCases(batchId?: string): Promise<CaseDetail[]> {
  try {
    const url = batchId ? `${API_BASE_URL}/api/cases?batch_id=${batchId}` : `${API_BASE_URL}/api/cases`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchPatterns(batchId?: string): Promise<PatternCluster[]> {
  try {
    const url = batchId ? `${API_BASE_URL}/api/patterns?batch_id=${batchId}` : `${API_BASE_URL}/api/patterns`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchCase(caseId: string): Promise<CaseDetail | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchAIExplanation(caseId: string, style: string = "standard"): Promise<AIExplainResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/explain?style=${encodeURIComponent(style)}`, {
      method: "POST",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export interface BenchmarkMetricGroup {
  batch_id: string;
  record_count: number;
  matched_count: number;
  exception_count: number;
  auto_resolved_count: number;
  human_review_count: number;
  unresolved_count: number;
  match_rate: number;
  enhanced_resolution_rate: number;
  throughput_records_per_sec: number;
  total_volume_inr: number;
  explained_volume_inr: number;
  unexplained_volume_inr: number;
  processing_time_ms: number;
  ground_truth_precision: number | null;
  ground_truth_recall: number | null;
  latent_hypothesis_accuracy: number | null;
  unsafe_resolutions_count: number;
  reason_code_breakdown?: Record<string, number>;
  scenario_breakdown?: Record<
    string,
    {
      total: number;
      exact_matches?: number;
      structured_cases?: number;
      auto_resolved?: number;
      human_review?: number;
      unresolved?: number;
      hypotheses_evaluated?: number;
      correct_hypotheses?: number;
      evaluation_mode?: string;
    }
  >;
}

export interface BenchmarkResponse {
  batch_id: string;
  records: number;
  baseline: BenchmarkMetricGroup;
  enhanced: BenchmarkMetricGroup;
  pattern_clusters?: PatternCluster[];
}

export async function fetchBenchmarkResults(
  rows: number = 10000,
  seed: number = 42,
  forceRefresh: boolean = false
): Promise<BenchmarkResponse | null> {
  try {
    const url = `${API_BASE_URL}/api/metrics/benchmark?rows=${rows}&seed=${seed}&force_refresh=${forceRefresh}`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function performCaseAction(
  caseId: string,
  action: string,
  operatorNotes?: string
): Promise<CaseDetail | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, operator_notes: operatorNotes }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export interface ChatCopilotResponse {
  response: string;
  provider: string;
  grounded_context?: string | null;
}

export async function chatCopilot(
  message: string,
  caseId?: string,
  batchId?: string
): Promise<ChatCopilotResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, case_id: caseId, batch_id: batchId }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

