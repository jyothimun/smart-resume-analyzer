export default function EmptyState({ hasJobs, onNew, onDemo }) {
  return (
    <section className="empty">
      <div className="empty-scan" aria-hidden="true">
        <div className="sheet"><i /><i /><i /><i /><i /><i /></div>
        <div className="beam" />
      </div>
      <h1>{hasJobs ? "Pick a job on the left" : "Screen your first batch of resumes"}</h1>
      <p className="muted">
        Add a job description, drop in PDF, DOCX or TXT resumes, and get them ranked by skill match,
        wording similarity and resume quality.
      </p>
      <div className="row center">
        <button className="btn primary" onClick={onNew}>Create a job</button>
        <button className="btn" onClick={onDemo}>Load demo data</button>
      </div>
    </section>
  );
}
