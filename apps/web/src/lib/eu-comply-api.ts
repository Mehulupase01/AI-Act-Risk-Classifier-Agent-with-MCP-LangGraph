export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  actor_type: string;
  organization: {
    id: string;
    slug: string;
    name: string;
  };
};

export type CaseSummary = {
  id: string;
  title: string;
  status: string;
  owner_team: string;
  policy_snapshot_slug: string | null;
  system_name: string;
  actor_role: string;
  created_at: string;
  updated_at: string;
};

export type CaseDetail = CaseSummary & {
  description: string | null;
  dossier: {
    id: string;
    case_id: string;
    system_name: string;
    actor_role: string;
    sector: string;
    intended_purpose: string;
    model_provider: string | null;
    model_name: string | null;
    uses_generative_ai: boolean;
    affects_natural_persons: boolean;
    geographic_scope: string[];
    deployment_channels: string[];
    human_oversight_summary: string | null;
    created_at: string;
    updated_at: string;
  };
};

export type ArtifactDetail = {
  id: string;
  case_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  status: string;
  parser_name: string | null;
  processing_error: string | null;
  created_at: string;
  updated_at: string;
  chunks: Array<{
    id: string;
    chunk_index: number;
    text_preview: string;
    char_start: number;
    char_end: number;
  }>;
  extracted_facts: Array<{
    id: string;
    field_path: string;
    value: unknown;
    confidence: number;
    extraction_method: string;
    status: string;
    rationale: string;
  }>;
};

type ArtifactSummary = {
  id: string;
  case_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type AssessmentRunDetail = {
  id: string;
  case_id: string;
  rule_pack_id: string;
  status: string;
  primary_outcome: string;
  created_at: string;
  summary: string;
  facts: Record<string, unknown>;
  conflict_fields: string[];
  hits: Array<{
    rule_id: string;
    title: string;
    outcome: string;
    priority: number;
    citation_refs: string[];
    obligation_tags: string[];
  }>;
  obligations: Array<{
    tag: string;
    title: string;
    description: string;
  }>;
};

export type WorkflowRunDetail = {
  id: string;
  case_id: string;
  assessment_run_id: string | null;
  status: string;
  review_required: boolean;
  review_reason: string | null;
  created_at: string;
  state: Record<string, unknown>;
};

export type ReviewDecisionSummary = {
  id: string;
  case_id: string;
  assessment_run_id: string | null;
  workflow_run_id: string | null;
  reviewer_identifier: string;
  decision: string;
  rationale: string;
  approved_outcome: string | null;
  created_at: string;
};

export type ReportExportResponse = {
  case_id: string;
  format: string;
  filename: string;
  media_type: string;
  content: string;
};

export type CaseCreatePayload = {
  title: string;
  description: string;
  owner_team: string;
  policy_snapshot_slug: string;
  dossier: {
    system_name: string;
    actor_role: string;
    sector: string;
    intended_purpose: string;
    model_provider?: string;
    model_name?: string;
    uses_generative_ai: boolean;
    affects_natural_persons: boolean;
    geographic_scope: string[];
    deployment_channels: string[];
    human_oversight_summary?: string;
  };
};

const DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1";

function normalizeBaseUrl(baseUrl: string) {
  const trimmed = baseUrl.trim();
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed || DEFAULT_BASE_URL;
}

async function requestJson<T>(
  path: string,
  options: RequestInit & { baseUrl: string; token?: string },
): Promise<T> {
  const { baseUrl, token, headers, ...rest } = options;
  const response = await fetch(`${normalizeBaseUrl(baseUrl)}${path}`, {
    ...rest,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      detail = await response.text();
    }
    throw new Error(detail || `Request failed with status ${response.status}.`);
  }

  return (await response.json()) as T;
}

export async function login(
  baseUrl: string,
  email: string,
  password: string,
): Promise<TokenResponse> {
  return requestJson<TokenResponse>("/auth/login", {
    baseUrl,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function listCases(baseUrl: string, token: string): Promise<CaseSummary[]> {
  return requestJson<CaseSummary[]>("/cases", { baseUrl, token });
}

export async function createCase(
  baseUrl: string,
  token: string,
  payload: CaseCreatePayload,
): Promise<CaseDetail> {
  return requestJson<CaseDetail>("/cases", {
    baseUrl,
    token,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getCase(
  baseUrl: string,
  token: string,
  caseId: string,
): Promise<CaseDetail> {
  return requestJson<CaseDetail>(`/cases/${caseId}`, { baseUrl, token });
}

export async function listArtifacts(
  baseUrl: string,
  token: string,
  caseId: string,
): Promise<ArtifactDetail[]> {
  const summaries = await requestJson<ArtifactSummary[]>(`/cases/${caseId}/artifacts`, {
    baseUrl,
    token,
  });
  return Promise.all(
    summaries.map((artifact) =>
      requestJson<ArtifactDetail>(`/cases/${caseId}/artifacts/${artifact.id}`, {
        baseUrl,
        token,
      }),
    ),
  );
}

export async function uploadArtifact(
  baseUrl: string,
  token: string,
  caseId: string,
  file: File,
): Promise<ArtifactDetail> {
  const body = new FormData();
  body.append("file", file);

  return requestJson<ArtifactDetail>(`/cases/${caseId}/artifacts`, {
    baseUrl,
    token,
    method: "POST",
    body,
  });
}

export async function processArtifact(
  baseUrl: string,
  token: string,
  caseId: string,
  artifactId: string,
): Promise<{ artifact: ArtifactDetail }> {
  return requestJson<{ artifact: ArtifactDetail }>(
    `/cases/${caseId}/artifacts/${artifactId}/process`,
    {
      baseUrl,
      token,
      method: "POST",
    },
  );
}

export async function listAssessments(
  baseUrl: string,
  token: string,
  caseId: string,
): Promise<AssessmentRunDetail[]> {
  return requestJson<AssessmentRunDetail[]>(`/cases/${caseId}/assessments`, {
    baseUrl,
    token,
  });
}

export async function runAssessment(
  baseUrl: string,
  token: string,
  caseId: string,
): Promise<AssessmentRunDetail> {
  return requestJson<AssessmentRunDetail>(`/cases/${caseId}/assessments`, {
    baseUrl,
    token,
    method: "POST",
  });
}

export async function listWorkflows(
  baseUrl: string,
  token: string,
  caseId: string,
): Promise<WorkflowRunDetail[]> {
  return requestJson<WorkflowRunDetail[]>(`/cases/${caseId}/workflow-runs`, {
    baseUrl,
    token,
  });
}

export async function runWorkflow(
  baseUrl: string,
  token: string,
  caseId: string,
): Promise<WorkflowRunDetail> {
  return requestJson<WorkflowRunDetail>(`/cases/${caseId}/workflow-runs`, {
    baseUrl,
    token,
    method: "POST",
  });
}

export async function listReviews(
  baseUrl: string,
  token: string,
  caseId: string,
): Promise<ReviewDecisionSummary[]> {
  return requestJson<ReviewDecisionSummary[]>(`/cases/${caseId}/reviews`, {
    baseUrl,
    token,
  });
}

export async function createReview(
  baseUrl: string,
  token: string,
  caseId: string,
  payload: {
    assessment_run_id?: string;
    workflow_run_id?: string;
    decision: "approved" | "needs_changes";
    rationale: string;
    approved_outcome?: string;
  },
): Promise<ReviewDecisionSummary> {
  return requestJson<ReviewDecisionSummary>(`/cases/${caseId}/reviews`, {
    baseUrl,
    token,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function exportReport(
  baseUrl: string,
  token: string,
  caseId: string,
  format: "json" | "markdown",
): Promise<ReportExportResponse> {
  return requestJson<ReportExportResponse>(`/cases/${caseId}/reports/export`, {
    baseUrl,
    token,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format }),
  });
}

export { DEFAULT_BASE_URL };
