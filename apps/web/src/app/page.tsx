import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.kicker}>EU-Comply</p>
          <h1>AI governance built for evidence, review, and real EU compliance work.</h1>
        </div>
        <a className={styles.consoleLink} href="/cases">
          Open Analyst Shell
        </a>
      </header>

      <main className={styles.main}>
        <section className={styles.heroCard}>
          <div className={styles.heroCopy}>
            <p className={styles.badge}>Flagship Build In Progress</p>
            <h2>Not a classifier bot. A governed AI Act assessment platform.</h2>
            <p>
              EU-Comply is being built as an enterprise-grade AI governance system
              with deterministic policy logic, audit-ready outputs, human review
              gates, and provider-agnostic LLM support across OpenRouter and Ollama.
            </p>
          </div>

          <div className={styles.runtimePanel}>
            <span>Runtime Control</span>
            <ul>
              <li>OpenRouter hosted inference</li>
              <li>Ollama local chat + embeddings</li>
              <li>Deterministic fallback when no LLM is available</li>
            </ul>
          </div>
        </section>

        <section className={styles.grid}>
          <article className={styles.card}>
            <span className={styles.cardLabel}>Verified Tonight</span>
            <h3>Foundation, auth, and runtime control</h3>
            <p>
              The repo now has a real FastAPI control plane, org-scoped persistence,
              JWT auth, audit foundations, runtime configuration, and provider
              adapters for OpenRouter and Ollama.
            </p>
          </article>

          <article className={styles.card}>
            <span className={styles.cardLabel}>Next Build Slice</span>
            <h3>Policy snapshots and deterministic rule engine</h3>
            <p>
              The next phases move into the real legal core: policy ingestion,
              policy-as-code, dossier intake, fact extraction, and obligations.
            </p>
          </article>

          <article className={styles.card}>
            <span className={styles.cardLabel}>Product Direction</span>
            <h3>Enterprise GRC first</h3>
            <p>
              The product is designed for compliance, legal, and AI governance
              teams, with evidence-first workflows and human approvals instead of
              autonomous legal claims.
            </p>
          </article>
        </section>
      </main>
    </div>
  );
}
