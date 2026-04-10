export default function CasesPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "32px",
      }}
    >
      <section
        style={{
          width: "min(760px, 100%)",
          padding: "32px",
          borderRadius: "24px",
          background: "rgba(255, 252, 247, 0.88)",
          border: "1px solid rgba(34, 31, 27, 0.08)",
          boxShadow: "var(--card-shadow)",
        }}
      >
        <p
          style={{
            marginBottom: "12px",
            color: "var(--forest-700)",
            textTransform: "uppercase",
            letterSpacing: "0.16em",
            fontSize: "0.82rem",
          }}
        >
          Analyst Shell
        </p>
        <h1
          style={{
            marginBottom: "14px",
            fontSize: "clamp(2rem, 5vw, 3.2rem)",
            lineHeight: 1,
            letterSpacing: "-0.04em",
          }}
        >
          Case workspace wiring starts after the policy and assessment core.
        </h1>
        <p style={{ color: "var(--ink-600)", lineHeight: 1.7 }}>
          The repo now has the verified backend foundation for auth, tenant-aware
          runtime control, and provider selection. The next meaningful UI step is
          a real evidence-first case workbench once case registry, dossier intake,
          and deterministic assessment routes are in place.
        </p>
      </section>
    </main>
  );
}
