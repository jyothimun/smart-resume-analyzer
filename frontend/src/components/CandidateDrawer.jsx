import { useEffect, useState } from "react";
import { api } from "../api";
import ScoreDial from "./ScoreDial.jsx";

const HEADINGS = ["Summary", "Strengths", "Gaps", "Interview questions"];

function parseInsights(text) {
  const blocks = [];
  let cur = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const h = HEADINGS.find((x) => line.toLowerCase().replace(/[*#]/g, "").startsWith(x.toLowerCase() + ":"));
    if (h) {
      cur = { title: h, items: [], para: "" };
      blocks.push(cur);
      const rest = line.replace(/[*#]/g, "").slice(h.length + 1).trim();
      if (rest) cur.para = rest;
    } else if (cur && line.startsWith("- ")) {
      cur.items.push(line.slice(2));
    } else if (cur) {
      cur.para = cur.para ? cur.para + " " + line : line;
    }
  }
  return blocks;
}

function Chips({ items, kind }) {
  if (!items.length) return <span className="muted small">None</span>;
  return (
    <div className="chips">
      {items.map((s) => <span key={s} className={`chip ${kind}`}>{s}</span>)}
    </div>
  );
}

function Meter({ label, value, hint }) {
  return (
    <div className="meter" title={hint}>
      <div className="meter-top"><span>{label}</span><b className="num">{Math.round(value)}%</b></div>
      <div className="bar"><span className="accent" style={{ width: `${value}%` }} /></div>
    </div>
  );
}

export default function CandidateDrawer({ candidateId, onClose, onDeleted, notify, aiEnabled }) {
  const [c, setC] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [showText, setShowText] = useState(false);

  useEffect(() => {
    setC(null);
    setShowText(false);
    api.getCandidate(candidateId).then(setC).catch((e) => notify(e.message, "error"));
  }, [candidateId, notify]);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function generate() {
    setLoadingAI(true);
    try {
      const res = await api.insights(candidateId);
      setC((prev) => ({ ...prev, insights: res.insights, insights_src: res.insights_src }));
    } catch (e) {
      notify(e.message, "error");
    } finally {
      setLoadingAI(false);
    }
  }

  async function remove() {
    if (!window.confirm(`Remove ${c.name} from this job?`)) return;
    try {
      await api.deleteCandidate(candidateId);
      await onDeleted();
    } catch (e) {
      notify(e.message, "error");
    }
  }

  return (
    <div className="overlay side" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-label="Candidate details">
        <button className="btn ghost close" onClick={onClose} aria-label="Close">Close</button>

        {!c ? (
          <p className="muted pad">Loading…</p>
        ) : (
          <>
            <div className="dhead">
              <ScoreDial score={c.score} />
              <div>
                <h2>{c.name}</h2>
                <p className="muted small">
                  {[c.email, c.phone, c.years_exp != null && `${c.years_exp} yrs experience`].filter(Boolean).join(" · ") || c.filename}
                </p>
                <span className={`pill ${c.score >= 75 ? "strong" : c.score >= 55 ? "good" : c.score >= 35 ? "partial" : "weak"}`}>{c.verdict}</span>
              </div>
            </div>

            <section>
              <h3>How the score was built</h3>
              <Meter label="Skill match" value={c.skill_score} hint="Share of the job's required skills found in the resume (55% of score)" />
              <Meter label="Wording similarity" value={c.text_score} hint="TF-IDF cosine similarity to the job description (35% of score)" />
              <Meter label="Resume quality" value={c.quality_score} hint="Contact details, key sections, sensible length (10% of score)" />
            </section>

            <section>
              <h3>Skills found</h3>
              <Chips items={c.matched} kind="ok" />
            </section>
            <section>
              <h3>Skills missing</h3>
              <Chips items={c.missing} kind="miss" />
            </section>
            {c.extra.length > 0 && (
              <section>
                <h3>Other skills on the resume</h3>
                <Chips items={c.extra} kind="extra" />
              </section>
            )}
            {c.keywords.length > 0 && (
              <section>
                <h3>Shared keywords with the job post</h3>
                <p className="small muted">{c.keywords.join(", ")}</p>
              </section>
            )}

            <section>
              <div className="row between">
                <h3>Insights</h3>
                {c.insights_src && (
                  <span className="muted small">{c.insights_src === "claude" ? "Written by Claude" : "Built-in analysis"}</span>
                )}
              </div>
              {c.insights ? (
                <div className="insights">
                  {parseInsights(c.insights).map((b) => (
                    <div key={b.title}>
                      <h4>{b.title}</h4>
                      {b.para && <p>{b.para}</p>}
                      {b.items.length > 0 && <ul>{b.items.map((t, i) => <li key={i}>{t}</li>)}</ul>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted small">
                  {aiEnabled
                    ? "Ask Claude for a summary, strengths, gaps and interview questions for this resume."
                    : "Get a summary, strengths, gaps and interview questions. Add an Anthropic API key in backend/.env for Claude-written insights."}
                </p>
              )}
              <button className="btn" onClick={generate} disabled={loadingAI}>
                {loadingAI ? "Analyzing…" : c.insights ? "Regenerate insights" : "Generate insights"}
              </button>
            </section>

            <section>
              <button className="btn ghost" onClick={() => setShowText((v) => !v)}>
                {showText ? "Hide resume text" : "Show extracted resume text"}
              </button>
              {showText && <pre className="resume-text">{c.resume_text}</pre>}
            </section>

            <div className="row end drawer-foot">
              <button className="btn danger ghost" onClick={remove}>Remove candidate</button>
            </div>
          </>
        )}
      </aside>
    </div>
  );
}
