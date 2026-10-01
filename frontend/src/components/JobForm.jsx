import { useState } from "react";

export default function JobForm({ onClose, onCreate }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [skills, setSkills] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit() {
    setErr("");
    setBusy(true);
    try {
      await onCreate({ title, description, skills });
    } catch (e) {
      setErr(e.message);
      setBusy(false);
    }
  }

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="jobform-title">
        <h2 id="jobform-title">New job</h2>

        <label htmlFor="jf-title">Job title</label>
        <input id="jf-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Full Stack Developer Associate" autoFocus />

        <label htmlFor="jf-desc">Job description</label>
        <textarea id="jf-desc" rows={9} value={description} onChange={(e) => setDescription(e.target.value)}
          placeholder="Paste the full job post: responsibilities, requirements, tools…" />

        <label htmlFor="jf-skills">
          Required skills <span className="muted">(optional, comma separated)</span>
        </label>
        <input id="jf-skills" value={skills} onChange={(e) => setSkills(e.target.value)}
          placeholder="Leave empty to detect skills from the description" />

        {err && <p className="form-error" role="alert">{err}</p>}

        <div className="row end">
          <button className="btn ghost" onClick={onClose} disabled={busy}>Cancel</button>
          <button className="btn primary" onClick={submit} disabled={busy}>
            {busy ? "Creating…" : "Create job"}
          </button>
        </div>
      </div>
    </div>
  );
}
