import { useMemo, useState } from "react";
import { api } from "../api";
import UploadZone from "./UploadZone.jsx";
import { tier } from "./ScoreDial.jsx";

export default function JobView({ job, onChanged, onOpen, onDelete, notify }) {
  const [query, setQuery] = useState("");
  const [showJD, setShowJD] = useState(false);

  const list = useMemo(() => {
    const q = query.trim().toLowerCase();
    return job.candidates
      .map((c, i) => ({ ...c, rank: i + 1 }))
      .filter((c) => !q || (c.name || "").toLowerCase().includes(q) || (c.email || "").toLowerCase().includes(q));
  }, [job.candidates, query]);

  const strong = job.candidates.filter((c) => c.score >= 75).length;

  return (
    <div className="jobview">
      <header className="jobhead">
        <div>
          <h1>{job.title}</h1>
          <p className="muted small">
            Looking for: {job.skills.slice(0, 10).join(", ")}
            {job.skills.length > 10 && ` and ${job.skills.length - 10} more`}
          </p>
        </div>
        <div className="row">
          <button className="btn ghost" onClick={() => setShowJD((v) => !v)}>
            {showJD ? "Hide description" : "View description"}
          </button>
          <a className={`btn ${job.candidates.length ? "" : "disabled"}`} href={job.candidates.length ? api.exportUrl(job.id) : undefined}>
            Export CSV
          </a>
          <button className="btn danger ghost" onClick={onDelete}>Delete job</button>
        </div>
      </header>

      {showJD && <pre className="jd">{job.description}</pre>}

      <section className="stats" aria-label="Summary">
        <Stat label="Resumes screened" value={job.candidate_count} />
        <Stat label="Strong matches" value={strong} />
        <Stat label="Top score" value={job.top_score != null ? Math.round(job.top_score) : "–"} />
        <Stat label="Average score" value={job.avg_score != null ? Math.round(job.avg_score) : "–"} />
      </section>

      <UploadZone jobId={job.id} onDone={onChanged} notify={notify} />

      {job.candidates.length === 0 ? (
        <p className="muted pad center">No resumes yet. Drop some above and they will appear here, best match first.</p>
      ) : (
        <section className="tablewrap">
          <div className="tablebar">
            <h2>Ranking</h2>
            <input className="search" placeholder="Search name or email" value={query}
              onChange={(e) => setQuery(e.target.value)} aria-label="Search candidates" />
          </div>
          <table className="table">
            <thead>
              <tr>
                <th className="c-rank">#</th>
                <th>Candidate</th>
                <th className="c-score">Score</th>
                <th>Verdict</th>
                <th>Required skills</th>
              </tr>
            </thead>
            <tbody>
              {list.map((c) => (
                <tr key={c.id} tabIndex={0} onClick={() => onOpen(c.id)}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onOpen(c.id)}>
                  <td className="c-rank">{c.rank}</td>
                  <td>
                    <div className="cname">{c.name}</div>
                    <div className="muted small">{c.email || c.filename}</div>
                  </td>
                  <td className="c-score">
                    <div className="scorecell">
                      <div className="bar"><span className={tier(c.score)} style={{ width: `${c.score}%` }} /></div>
                      <b className="num">{c.score.toFixed(1)}</b>
                    </div>
                  </td>
                  <td><span className={`pill ${tier(c.score)}`}>{c.verdict}</span></td>
                  <td className="num">
                    {c.matched.length} / {c.matched.length + c.missing.length}
                  </td>
                </tr>
              ))}
              {list.length === 0 && (
                <tr><td colSpan={5} className="muted center pad">No candidates match “{query}”.</td></tr>
              )}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <div className="stat-value num">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
