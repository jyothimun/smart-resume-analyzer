export default function Sidebar({ jobs, activeId, onSelect, onNew, health }) {
  const status =
    health === null ? { cls: "wait", text: "Connecting…" }
    : health === false ? { cls: "off", text: "Backend offline" }
    : health.ai_enabled ? { cls: "on", text: "Online · Claude insights on" }
    : { cls: "on", text: "Online · built-in insights" };

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true" />
        <div>
          <div className="brand-name">Resume Screener</div>
          <div className="brand-sub">Rank resumes against a job</div>
        </div>
      </div>

      <button className="btn primary block" onClick={onNew}>New job</button>

      <nav className="joblist" aria-label="Jobs">
        {jobs.length === 0 && <p className="muted small pad">No jobs yet. Create one to start screening.</p>}
        {jobs.map((j) => (
          <button
            key={j.id}
            className={`jobitem ${j.id === activeId ? "active" : ""}`}
            onClick={() => onSelect(j.id)}
          >
            <span className="jobitem-title">{j.title}</span>
            <span className="jobitem-meta">
              {j.candidate_count} {j.candidate_count === 1 ? "resume" : "resumes"}
              {j.top_score != null && <> · top {Math.round(j.top_score)}</>}
            </span>
          </button>
        ))}
      </nav>

      <div className={`status ${status.cls}`}>
        <span className="dot" />
        {status.text}
      </div>
    </aside>
  );
}
