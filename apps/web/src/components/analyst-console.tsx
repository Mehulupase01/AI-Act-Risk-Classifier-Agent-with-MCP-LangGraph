"use client";

import { type FormEvent, useDeferredValue, useEffect, useState, useTransition } from "react";

import styles from "./analyst-console.module.css";
import {
  type ArtifactDetail,
  type AssessmentRunDetail,
  type CaseCreatePayload,
  type CaseDetail,
  type CaseSummary,
  DEFAULT_BASE_URL,
  type ReviewDecisionSummary,
  type WorkflowRunDetail,
  exportAuditPack,
  createReview,
  createCase,
  exportReport,
  getCase,
  listArtifacts,
  listAssessments,
  listCases,
  listReviews,
  listWorkflows,
  login,
  processArtifact,
  runAssessment,
  runWorkflow,
  uploadArtifact,
} from "@/lib/eu-comply-api";

type NoticeTone = "info" | "success" | "error";

type Notice = {
  tone: NoticeTone;
  text: string;
};

const STORAGE_KEYS = {
  baseUrl: "eu-comply.base-url",
  token: "eu-comply.token",
  orgName: "eu-comply.org-name",
  email: "eu-comply.email",
};

const DEFAULT_CASE_FORM: CaseCreatePayload = {
  title: "Hiring Screening Assistant",
  description: "AI-supported screening workspace for recruiter triage.",
  owner_team: "AI Governance",
  policy_snapshot_slug: "eu-ai-act-baseline-2026-04-10",
  dossier: {
    system_name: "Candidate Screening Assistant",
    actor_role: "provider",
    sector: "employment",
    intended_purpose:
      "Assist recruiters with candidate screening, triage, and prioritization before human review.",
    model_provider: "OpenAI",
    model_name: "gpt-4.1-mini",
    uses_generative_ai: true,
    affects_natural_persons: true,
    geographic_scope: ["EU"],
    deployment_channels: ["internal_web_app"],
    human_oversight_summary:
      "Recruiters review every recommendation before a decision is made.",
  },
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatList(items: string[]) {
  return items.length ? items.join(", ") : "None recorded";
}

function valueToText(value: unknown) {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value);
  }
  return String(value);
}

function downloadTextFile(filename: string, content: string, mediaType: string) {
  const blob = new Blob([content], { type: mediaType });
  const downloadUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = downloadUrl;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

function downloadBase64File(filename: string, contentBase64: string, mediaType: string) {
  const binary = window.atob(contentBase64);
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  const blob = new Blob([bytes], { type: mediaType });
  const downloadUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = downloadUrl;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export function AnalystConsole() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [email, setEmail] = useState("admin@eucomply.dev");
  const [password, setPassword] = useState("change-me-now");
  const [token, setToken] = useState<string | null>(null);
  const [organizationName, setOrganizationName] = useState("Disconnected");
  const [notice, setNotice] = useState<Notice>({
    tone: "info",
    text: "Connect the console to the FastAPI control plane to operate real cases.",
  });
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedCase, setSelectedCase] = useState<CaseDetail | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactDetail[]>([]);
  const [assessments, setAssessments] = useState<AssessmentRunDetail[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowRunDetail[]>([]);
  const [reviews, setReviews] = useState<ReviewDecisionSummary[]>([]);
  const [caseSearch, setCaseSearch] = useState("");
  const [caseForm, setCaseForm] = useState(DEFAULT_CASE_FORM);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [reviewDecision, setReviewDecision] = useState<"approved" | "needs_changes">("approved");
  const [reviewRationale, setReviewRationale] = useState(
    "Compliance reviewer assessed the latest governed outcome with supporting evidence.",
  );
  const [reviewOutcome, setReviewOutcome] = useState("high_risk");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const deferredSearch = useDeferredValue(caseSearch);

  const filteredCases = cases.filter((item) => {
    const query = deferredSearch.trim().toLowerCase();
    if (!query) {
      return true;
    }
    return `${item.title} ${item.system_name} ${item.owner_team}`.toLowerCase().includes(query);
  });
  const latestAssessment = assessments[0] ?? null;
  const latestWorkflow = workflows[0] ?? null;
  const reviewTargetLabel = latestWorkflow
    ? "latest workflow run"
    : latestAssessment
      ? "latest assessment run"
      : null;

  async function loadCaseWorkspace(caseId: string, authToken = token, apiBaseUrl = baseUrl) {
    if (!authToken) {
      return;
    }
    setBusyAction("refresh-case");
    try {
      const [detail, nextArtifacts, nextAssessments, nextWorkflows, nextReviews] = await Promise.all([
        getCase(apiBaseUrl, authToken, caseId),
        listArtifacts(apiBaseUrl, authToken, caseId),
        listAssessments(apiBaseUrl, authToken, caseId),
        listWorkflows(apiBaseUrl, authToken, caseId),
        listReviews(apiBaseUrl, authToken, caseId),
      ]);
      startTransition(() => {
        setSelectedCase(detail);
        setArtifacts(nextArtifacts);
        setAssessments(nextAssessments);
        setWorkflows(nextWorkflows);
        setReviews(nextReviews);
      });
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to load case workspace.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function refreshCases(authToken = token, apiBaseUrl = baseUrl, preferredCaseId?: string) {
    if (!authToken) {
      return;
    }
    setBusyAction("refresh-cases");
    try {
      const nextCases = await listCases(apiBaseUrl, authToken);
      const nextSelectedCaseId =
        preferredCaseId ??
        (selectedCaseId && nextCases.some((item) => item.id === selectedCaseId)
          ? selectedCaseId
          : nextCases[0]?.id ?? null);

      startTransition(() => {
        setCases(nextCases);
        setSelectedCaseId(nextSelectedCaseId);
        if (!nextSelectedCaseId) {
          setSelectedCase(null);
          setArtifacts([]);
          setAssessments([]);
          setWorkflows([]);
          setReviews([]);
        }
      });

      if (nextSelectedCaseId) {
        await loadCaseWorkspace(nextSelectedCaseId, authToken, apiBaseUrl);
      }
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to refresh cases.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  useEffect(() => {
    const savedBaseUrl = window.localStorage.getItem(STORAGE_KEYS.baseUrl);
    const savedToken = window.localStorage.getItem(STORAGE_KEYS.token);
    const savedOrganizationName = window.localStorage.getItem(STORAGE_KEYS.orgName);
    const savedEmail = window.localStorage.getItem(STORAGE_KEYS.email);

    if (savedBaseUrl) {
      setBaseUrl(savedBaseUrl);
    }
    if (savedEmail) {
      setEmail(savedEmail);
    }
    if (savedToken) {
      setToken(savedToken);
      setOrganizationName(savedOrganizationName ?? "Connected");
      void (async () => {
        setBusyAction("refresh-cases");
        try {
          const resolvedBaseUrl = savedBaseUrl ?? DEFAULT_BASE_URL;
          const nextCases = await listCases(resolvedBaseUrl, savedToken);
          const nextSelectedCaseId = nextCases[0]?.id ?? null;

          startTransition(() => {
            setCases(nextCases);
            setSelectedCaseId(nextSelectedCaseId);
          });

          if (nextSelectedCaseId) {
            const [detail, nextArtifacts, nextAssessments, nextWorkflows, nextReviews] =
              await Promise.all([
                getCase(resolvedBaseUrl, savedToken, nextSelectedCaseId),
                listArtifacts(resolvedBaseUrl, savedToken, nextSelectedCaseId),
                listAssessments(resolvedBaseUrl, savedToken, nextSelectedCaseId),
                listWorkflows(resolvedBaseUrl, savedToken, nextSelectedCaseId),
                listReviews(resolvedBaseUrl, savedToken, nextSelectedCaseId),
              ]);
            startTransition(() => {
              setSelectedCase(detail);
              setArtifacts(nextArtifacts);
              setAssessments(nextAssessments);
              setWorkflows(nextWorkflows);
              setReviews(nextReviews);
            });
          }
        } catch (error) {
          setNotice({
            tone: "error",
            text:
              error instanceof Error
                ? error.message
                : "Failed to restore the previous console session.",
          });
        } finally {
          setBusyAction(null);
        }
      })();
    }
  }, [startTransition]);

  async function handleSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction("sign-in");
    try {
      const session = await login(baseUrl, email, password);
      window.localStorage.setItem(STORAGE_KEYS.baseUrl, baseUrl);
      window.localStorage.setItem(STORAGE_KEYS.token, session.access_token);
      window.localStorage.setItem(STORAGE_KEYS.orgName, session.organization.name);
      window.localStorage.setItem(STORAGE_KEYS.email, email);
      startTransition(() => {
        setToken(session.access_token);
        setOrganizationName(session.organization.name);
      });
      setNotice({
        tone: "success",
        text: `Connected to ${session.organization.name}. Loading live cases...`,
      });
      await refreshCases(session.access_token, baseUrl);
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to sign in.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  function handleSignOut() {
    window.localStorage.removeItem(STORAGE_KEYS.token);
    window.localStorage.removeItem(STORAGE_KEYS.orgName);
    startTransition(() => {
      setToken(null);
      setOrganizationName("Disconnected");
      setCases([]);
      setSelectedCaseId(null);
      setSelectedCase(null);
      setArtifacts([]);
      setAssessments([]);
      setWorkflows([]);
      setReviews([]);
    });
    setNotice({
      tone: "info",
      text: "Signed out. You can reconnect with the backend at any time.",
    });
  }

  useEffect(() => {
    if (assessments[0]?.primary_outcome) {
      setReviewOutcome(assessments[0].primary_outcome);
    }
  }, [assessments]);

  async function handleCreateCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }
    setBusyAction("create-case");
    try {
      const created = await createCase(baseUrl, token, caseForm);
      setNotice({
        tone: "success",
        text: `Created case '${created.title}'.`,
      });
      await refreshCases(token, baseUrl, created.id);
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to create case.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleSelectCase(caseId: string) {
    if (!token) {
      return;
    }
    startTransition(() => setSelectedCaseId(caseId));
    await loadCaseWorkspace(caseId, token, baseUrl);
  }

  async function handleUploadArtifact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedCaseId || !uploadFile) {
      return;
    }
    setBusyAction("upload-artifact");
    try {
      await uploadArtifact(baseUrl, token, selectedCaseId, uploadFile);
      setUploadFile(null);
      setNotice({
        tone: "success",
        text: `Uploaded '${uploadFile.name}'.`,
      });
      await loadCaseWorkspace(selectedCaseId, token, baseUrl);
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to upload artifact.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleProcessArtifact(artifactId: string) {
    if (!token || !selectedCaseId) {
      return;
    }
    setBusyAction(`process:${artifactId}`);
    try {
      await processArtifact(baseUrl, token, selectedCaseId, artifactId);
      setNotice({
        tone: "success",
        text: "Artifact parsed, chunked, and added to extracted facts.",
      });
      await loadCaseWorkspace(selectedCaseId, token, baseUrl);
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to process artifact.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRunAssessment() {
    if (!token || !selectedCaseId) {
      return;
    }
    setBusyAction("run-assessment");
    try {
      const assessment = await runAssessment(baseUrl, token, selectedCaseId);
      setNotice({
        tone: "success",
        text: `Assessment completed with outcome '${assessment.primary_outcome}'.`,
      });
      await loadCaseWorkspace(selectedCaseId, token, baseUrl);
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to run assessment.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRunWorkflow() {
    if (!token || !selectedCaseId) {
      return;
    }
    setBusyAction("run-workflow");
    try {
      const workflow = await runWorkflow(baseUrl, token, selectedCaseId);
      setNotice({
        tone: workflow.review_required ? "info" : "success",
        text: workflow.review_required
          ? "Workflow routed this case into review-required state."
          : "Workflow completed without a review gate.",
      });
      await loadCaseWorkspace(selectedCaseId, token, baseUrl);
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to run workflow.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleCreateReview() {
    if (!token || !selectedCaseId || !reviewTargetLabel) {
      return;
    }
    setBusyAction("create-review");
    try {
      const payload: {
        assessment_run_id?: string;
        workflow_run_id?: string;
        decision: "approved" | "needs_changes";
        rationale: string;
        approved_outcome?: string;
      } = {
        decision: reviewDecision,
        rationale: reviewRationale,
      };
      if (latestWorkflow?.id) {
        payload.workflow_run_id = latestWorkflow.id;
      }
      if (latestWorkflow?.assessment_run_id) {
        payload.assessment_run_id = latestWorkflow.assessment_run_id;
      } else if (latestAssessment?.id) {
        payload.assessment_run_id = latestAssessment.id;
      }
      if (reviewDecision === "approved") {
        payload.approved_outcome = reviewOutcome;
      }

      await createReview(baseUrl, token, selectedCaseId, payload);
      setNotice({
        tone: reviewDecision === "approved" ? "success" : "info",
        text:
          reviewDecision === "approved"
            ? "Review approved and written to the approval ledger."
            : "Review recorded with requested changes.",
      });
      await loadCaseWorkspace(selectedCaseId, token, baseUrl);
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to submit review.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleExportReport(format: "json" | "markdown") {
    if (!token || !selectedCaseId) {
      return;
    }
    setBusyAction(`export:${format}`);
    try {
      const report = await exportReport(baseUrl, token, selectedCaseId, format);
      downloadTextFile(report.filename, report.content, report.media_type);
      setNotice({
        tone: "success",
        text: `Exported ${format.toUpperCase()} report '${report.filename}'.`,
      });
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to export report.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleExportAuditPack() {
    if (!token || !selectedCaseId) {
      return;
    }
    setBusyAction("export:audit-pack");
    try {
      const auditPack = await exportAuditPack(baseUrl, token, selectedCaseId);
      downloadBase64File(
        auditPack.filename,
        auditPack.content_base64,
        auditPack.media_type,
      );
      setNotice({
        tone: "success",
        text: `Exported audit pack '${auditPack.filename}' with ${auditPack.manifest.files.length} bundled files.`,
      });
    } catch (error) {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Failed to export audit pack.",
      });
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.kicker}>Analyst Console</p>
          <h1>Operate live EU AI Act cases with evidence, decisions, and review gates.</h1>
        </div>
        <div className={styles.statusRail}>
          <span className={styles.connectionPill}>{organizationName}</span>
          {token ? (
            <button className={styles.secondaryButton} onClick={handleSignOut} type="button">
              Sign out
            </button>
          ) : null}
        </div>
      </header>

      <section className={`${styles.notice} ${styles[`notice${notice.tone}`]}`}>
        <strong>{notice.tone.toUpperCase()}</strong>
        <span>{notice.text}</span>
      </section>

      {!token ? (
        <section className={styles.authShell}>
          <article className={styles.panel}>
            <span className={styles.panelLabel}>Backend Session</span>
            <h2>Connect this console to the FastAPI control plane.</h2>
            <p className={styles.panelCopy}>
              The UI is now wired to the live backend routes for cases, artifacts,
              assessments, and workflows. Use the bootstrap credentials below in
              local development, or replace them with real environment values.
            </p>
            <form className={styles.authForm} onSubmit={handleSignIn}>
              <label className={styles.field}>
                <span>API Base URL</span>
                <input
                  onChange={(event) => setBaseUrl(event.target.value)}
                  value={baseUrl}
                />
              </label>
              <label className={styles.field}>
                <span>Email</span>
                <input onChange={(event) => setEmail(event.target.value)} value={email} />
              </label>
              <label className={styles.field}>
                <span>Password</span>
                <input
                  onChange={(event) => setPassword(event.target.value)}
                  type="password"
                  value={password}
                />
              </label>
              <button
                className={styles.primaryButton}
                disabled={busyAction === "sign-in"}
                type="submit"
              >
                {busyAction === "sign-in" ? "Connecting..." : "Sign in"}
              </button>
            </form>
          </article>
        </section>
      ) : (
        <section className={styles.workspace}>
          <aside className={styles.sidebar}>
            <article className={styles.panel}>
              <span className={styles.panelLabel}>Connection</span>
              <div className={styles.metricBlock}>
                <span className={styles.metricLabel}>API</span>
                <p className={styles.metricValue}>{baseUrl}</p>
              </div>
              <div className={styles.metricGrid}>
                <div className={styles.metricCard}>
                  <span>Cases</span>
                  <strong>{cases.length}</strong>
                </div>
                <div className={styles.metricCard}>
                  <span>Loaded</span>
                  <strong>{selectedCase ? "1" : "0"}</strong>
                </div>
              </div>
              <button
                className={styles.secondaryButton}
                disabled={busyAction === "refresh-cases"}
                onClick={() => void refreshCases()}
                type="button"
              >
                Refresh Workspace
              </button>
            </article>

            <article className={styles.panel}>
              <span className={styles.panelLabel}>Create Case</span>
              <form className={styles.caseForm} onSubmit={handleCreateCase}>
                <label className={styles.field}>
                  <span>Title</span>
                  <input
                    onChange={(event) =>
                      setCaseForm((current) => ({ ...current, title: event.target.value }))
                    }
                    value={caseForm.title}
                  />
                </label>
                <label className={styles.field}>
                  <span>Owner Team</span>
                  <input
                    onChange={(event) =>
                      setCaseForm((current) => ({ ...current, owner_team: event.target.value }))
                    }
                    value={caseForm.owner_team}
                  />
                </label>
                <label className={styles.field}>
                  <span>Sector</span>
                  <input
                    onChange={(event) =>
                      setCaseForm((current) => ({
                        ...current,
                        dossier: { ...current.dossier, sector: event.target.value },
                      }))
                    }
                    value={caseForm.dossier.sector}
                  />
                </label>
                <label className={styles.field}>
                  <span>Purpose</span>
                  <textarea
                    onChange={(event) =>
                      setCaseForm((current) => ({
                        ...current,
                        dossier: {
                          ...current.dossier,
                          intended_purpose: event.target.value,
                        },
                      }))
                    }
                    rows={5}
                    value={caseForm.dossier.intended_purpose}
                  />
                </label>
                <button
                  className={styles.primaryButton}
                  disabled={busyAction === "create-case"}
                  type="submit"
                >
                  {busyAction === "create-case" ? "Creating..." : "Create Case"}
                </button>
              </form>
            </article>

            <article className={styles.panel}>
              <div className={styles.panelHeader}>
                <span className={styles.panelLabel}>Cases</span>
                <input
                  className={styles.searchInput}
                  onChange={(event) => setCaseSearch(event.target.value)}
                  placeholder="Search cases"
                  value={caseSearch}
                />
              </div>
              <div className={styles.caseList}>
                {filteredCases.map((item) => (
                  <button
                    className={`${styles.caseListItem} ${
                      selectedCaseId === item.id ? styles.caseListItemActive : ""
                    }`}
                    key={item.id}
                    onClick={() => void handleSelectCase(item.id)}
                    type="button"
                  >
                    <div>
                      <strong>{item.title}</strong>
                      <span>{item.system_name}</span>
                    </div>
                    <small>{item.status.replaceAll("_", " ")}</small>
                  </button>
                ))}
                {!filteredCases.length ? (
                  <p className={styles.emptyCopy}>No cases match the current search.</p>
                ) : null}
              </div>
            </article>
          </aside>

          <section className={styles.mainColumn}>
            {selectedCase ? (
              <>
                <article className={styles.heroPanel}>
                  <div>
                    <span className={styles.panelLabel}>Selected Case</span>
                    <h2>{selectedCase.title}</h2>
                    <p>{selectedCase.description ?? "No case description provided yet."}</p>
                  </div>
                  <div className={styles.actionRail}>
                    <span className={styles.statusBadge}>{selectedCase.status.replaceAll("_", " ")}</span>
                    <button
                      className={styles.secondaryButton}
                      disabled={busyAction === "run-assessment"}
                      onClick={() => void handleRunAssessment()}
                      type="button"
                    >
                      {busyAction === "run-assessment" ? "Running..." : "Run Assessment"}
                    </button>
                    <button
                      className={styles.primaryButton}
                      disabled={busyAction === "run-workflow"}
                      onClick={() => void handleRunWorkflow()}
                      type="button"
                    >
                      {busyAction === "run-workflow" ? "Routing..." : "Run Workflow"}
                    </button>
                  </div>
                </article>

                <div className={styles.contentGrid}>
                  <article className={styles.panel}>
                    <span className={styles.panelLabel}>Dossier</span>
                    <div className={styles.metricGrid}>
                      <div className={styles.metricCard}>
                        <span>Actor</span>
                        <strong>{selectedCase.actor_role}</strong>
                      </div>
                      <div className={styles.metricCard}>
                        <span>Sector</span>
                        <strong>{selectedCase.dossier.sector}</strong>
                      </div>
                      <div className={styles.metricCard}>
                        <span>Generative</span>
                        <strong>{selectedCase.dossier.uses_generative_ai ? "Yes" : "No"}</strong>
                      </div>
                      <div className={styles.metricCard}>
                        <span>Geography</span>
                        <strong>{formatList(selectedCase.dossier.geographic_scope)}</strong>
                      </div>
                    </div>
                    <div className={styles.detailBlock}>
                      <h3>Purpose</h3>
                      <p>{selectedCase.dossier.intended_purpose}</p>
                    </div>
                    <div className={styles.detailBlock}>
                      <h3>Oversight</h3>
                      <p>
                        {selectedCase.dossier.human_oversight_summary ??
                          "No oversight summary recorded."}
                      </p>
                    </div>
                  </article>

                  <article className={styles.panel}>
                    <div className={styles.panelHeader}>
                      <span className={styles.panelLabel}>Evidence</span>
                      <small>{artifacts.length} artifacts</small>
                    </div>
                    <form className={styles.uploadForm} onSubmit={handleUploadArtifact}>
                      <label className={styles.field}>
                        <span>Upload Artifact</span>
                        <input
                          onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
                          type="file"
                        />
                      </label>
                      <button
                        className={styles.secondaryButton}
                        disabled={busyAction === "upload-artifact" || !uploadFile}
                        type="submit"
                      >
                        {busyAction === "upload-artifact" ? "Uploading..." : "Upload"}
                      </button>
                    </form>
                    <div className={styles.stack}>
                      {artifacts.map((artifact) => (
                        <section className={styles.itemCard} key={artifact.id}>
                          <div className={styles.itemHeader}>
                            <div>
                              <strong>{artifact.filename}</strong>
                              <span>
                                {artifact.status} | {formatDate(artifact.updated_at)}
                              </span>
                            </div>
                            <button
                              className={styles.secondaryButton}
                              disabled={busyAction === `process:${artifact.id}`}
                              onClick={() => void handleProcessArtifact(artifact.id)}
                              type="button"
                            >
                              {busyAction === `process:${artifact.id}` ? "Processing..." : "Process"}
                            </button>
                          </div>
                          <div className={styles.metaRow}>
                            <span>{artifact.parser_name ?? "Unparsed"}</span>
                            <span>{artifact.chunks.length} chunks</span>
                            <span>{artifact.extracted_facts.length} facts</span>
                          </div>
                          {artifact.processing_error ? (
                            <p className={styles.errorCopy}>{artifact.processing_error}</p>
                          ) : null}
                          {artifact.extracted_facts.length ? (
                            <ul className={styles.factList}>
                              {artifact.extracted_facts.map((fact) => (
                                <li key={fact.id}>
                                  <strong>{fact.field_path}</strong>
                                  <span>{valueToText(fact.value)}</span>
                                  <small>{fact.status}</small>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className={styles.emptyCopy}>
                              Processing will populate chunks and extracted facts here.
                            </p>
                          )}
                        </section>
                      ))}
                    </div>
                  </article>

                  <article className={styles.panel}>
                    <div className={styles.panelHeader}>
                      <span className={styles.panelLabel}>Assessments</span>
                      <small>{assessments.length} runs</small>
                    </div>
                    <div className={styles.stack}>
                      {assessments.map((assessment) => (
                        <section className={styles.itemCard} key={assessment.id}>
                          <div className={styles.itemHeader}>
                            <div>
                              <strong>{assessment.primary_outcome.replaceAll("_", " ")}</strong>
                              <span>{formatDate(assessment.created_at)}</span>
                            </div>
                            <span className={styles.statusBadge}>{assessment.status}</span>
                          </div>
                          <p className={styles.itemCopy}>{assessment.summary}</p>
                          <div className={styles.tagRow}>
                            {assessment.obligations.map((obligation) => (
                              <span className={styles.tag} key={obligation.tag}>
                                {obligation.title}
                              </span>
                            ))}
                          </div>
                          {assessment.conflict_fields.length ? (
                            <p className={styles.errorCopy}>
                              Conflicts: {assessment.conflict_fields.join(", ")}
                            </p>
                          ) : null}
                        </section>
                      ))}
                      {!assessments.length ? (
                        <p className={styles.emptyCopy}>
                          Run an assessment after processing evidence to generate a deterministic outcome.
                        </p>
                      ) : null}
                    </div>
                  </article>

                  <article className={styles.panel}>
                    <div className={styles.panelHeader}>
                      <span className={styles.panelLabel}>Workflows</span>
                      <small>{workflows.length} runs</small>
                    </div>
                    <div className={styles.stack}>
                      {workflows.map((workflow) => (
                        <section className={styles.itemCard} key={workflow.id}>
                          <div className={styles.itemHeader}>
                            <div>
                              <strong>{workflow.status.replaceAll("_", " ")}</strong>
                              <span>{formatDate(workflow.created_at)}</span>
                            </div>
                            <span
                              className={`${styles.statusBadge} ${
                                workflow.review_required ? styles.reviewBadge : ""
                              }`}
                            >
                              {workflow.review_required ? "review required" : "clear"}
                            </span>
                          </div>
                          <p className={styles.itemCopy}>
                            {workflow.review_reason ??
                              "No review gate was triggered in this workflow run."}
                          </p>
                          <code className={styles.codeBlock}>
                            {JSON.stringify(workflow.state, null, 2)}
                          </code>
                        </section>
                      ))}
                      {!workflows.length ? (
                        <p className={styles.emptyCopy}>
                          Run the governed workflow to capture review routing and durable state.
                        </p>
                      ) : null}
                    </div>
                  </article>

                  <article className={styles.panel}>
                    <div className={styles.panelHeader}>
                      <span className={styles.panelLabel}>Reviews And Reports</span>
                      <small>{reviews.length} review decisions</small>
                    </div>
                    <div className={styles.metricGrid}>
                      <div className={styles.metricCard}>
                        <span>Review Target</span>
                        <strong>{reviewTargetLabel ?? "No assessment yet"}</strong>
                      </div>
                      <div className={styles.metricCard}>
                        <span>Approved Outcome</span>
                        <strong>{reviews[0]?.approved_outcome ?? "Not approved yet"}</strong>
                      </div>
                    </div>
                    <div className={styles.detailBlock}>
                      <h3>Governance Actions</h3>
                      <p>
                        Record a human decision against the latest assessment or workflow, then export
                        the current assessment pack as JSON, Markdown, or a bundled audit archive.
                      </p>
                    </div>
                    <div className={styles.authForm}>
                      <label className={styles.field}>
                        <span>Decision</span>
                        <select
                          onChange={(event) =>
                            setReviewDecision(event.target.value as "approved" | "needs_changes")
                          }
                          value={reviewDecision}
                        >
                          <option value="approved">Approved</option>
                          <option value="needs_changes">Needs Changes</option>
                        </select>
                      </label>
                      <label className={styles.field}>
                        <span>Approved Outcome</span>
                        <select
                          disabled={reviewDecision !== "approved"}
                          onChange={(event) => setReviewOutcome(event.target.value)}
                          value={reviewOutcome}
                        >
                          <option value="out_of_scope">Out Of Scope</option>
                          <option value="prohibited">Prohibited</option>
                          <option value="high_risk">High Risk</option>
                          <option value="transparency_only">Transparency Only</option>
                          <option value="gpai_related">GPAI Related</option>
                          <option value="minimal_risk">Minimal Risk</option>
                          <option value="needs_more_information">Needs More Information</option>
                        </select>
                      </label>
                      <label className={styles.field}>
                        <span>Rationale</span>
                        <textarea
                          onChange={(event) => setReviewRationale(event.target.value)}
                          rows={4}
                          value={reviewRationale}
                        />
                      </label>
                      <div className={styles.actionRail}>
                        <button
                          className={styles.secondaryButton}
                          disabled={!reviewTargetLabel || busyAction === "create-review"}
                          onClick={() => void handleCreateReview()}
                          type="button"
                        >
                          {busyAction === "create-review" ? "Recording..." : "Record Review"}
                        </button>
                        <button
                          className={styles.secondaryButton}
                          disabled={busyAction === "export:json"}
                          onClick={() => void handleExportReport("json")}
                          type="button"
                        >
                          {busyAction === "export:json" ? "Exporting..." : "Export JSON"}
                        </button>
                        <button
                          className={styles.primaryButton}
                          disabled={busyAction === "export:markdown"}
                          onClick={() => void handleExportReport("markdown")}
                          type="button"
                        >
                          {busyAction === "export:markdown" ? "Exporting..." : "Export Markdown"}
                        </button>
                        <button
                          className={styles.primaryButton}
                          disabled={busyAction === "export:audit-pack"}
                          onClick={() => void handleExportAuditPack()}
                          type="button"
                        >
                          {busyAction === "export:audit-pack" ? "Exporting..." : "Export Audit Pack"}
                        </button>
                      </div>
                    </div>
                    <div className={styles.stack}>
                      {reviews.map((review) => (
                        <section className={styles.itemCard} key={review.id}>
                          <div className={styles.itemHeader}>
                            <div>
                              <strong>{review.decision.replaceAll("_", " ")}</strong>
                              <span>{formatDate(review.created_at)}</span>
                            </div>
                            <span className={styles.statusBadge}>
                              {review.approved_outcome ?? "no override"}
                            </span>
                          </div>
                          <p className={styles.itemCopy}>{review.rationale}</p>
                          <div className={styles.metaRow}>
                            <span>{review.reviewer_identifier}</span>
                            <span>{review.workflow_run_id ? "workflow-linked" : "assessment-linked"}</span>
                          </div>
                        </section>
                      ))}
                      {!reviews.length ? (
                        <p className={styles.emptyCopy}>
                          No review decisions recorded yet. Run a workflow and capture the first
                          approval or change request here.
                        </p>
                      ) : null}
                    </div>
                  </article>
                </div>
              </>
            ) : (
              <article className={styles.emptyState}>
                <span className={styles.panelLabel}>Operator Workspace</span>
                <h2>Select or create a case to begin.</h2>
                <p>
                  The console is now wired to the live backend. Once a case is selected,
                  you can upload evidence, process artifacts, trigger deterministic assessments,
                  and route the result through the governed workflow.
                </p>
              </article>
            )}
          </section>
        </section>
      )}

      <footer className={styles.footer}>
        <span>{isPending ? "Refreshing interface..." : "Interface synced with live backend routes."}</span>
        <span>Cases, evidence, assessments, workflows, reviews, and audit-pack exports are live surfaces now.</span>
      </footer>
    </main>
  );
}
