import { useRef, useState } from "react";
import { api } from "../api";

export default function UploadZone({ jobId, onDone, notify }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [problems, setProblems] = useState([]);

  async function send(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    setBusy(true);
    setProblems([]);
    try {
      const res = await api.uploadResumes(jobId, files);
      setProblems(res.errors || []);
      notify(`Screened ${res.added.length} ${res.added.length === 1 ? "resume" : "resumes"}.`);
      await onDone();
    } catch (e) {
      setProblems(e.body?.errors || []);
      notify(e.body?.errors?.length ? "No resumes could be read. See the list below." : e.message, "error");
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  return (
    <div>
      <div
        className={`dropzone ${over ? "over" : ""} ${busy ? "scanning" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); send(e.dataTransfer.files); }}
      >
        <div className="beam" aria-hidden="true" />
        <div className="dz-text">
          <strong>{busy ? "Scanning resumes…" : "Drop resumes here"}</strong>
          <span className="muted">PDF, DOCX or TXT · select many at once</span>
        </div>
        <button className="btn" disabled={busy} onClick={() => input.current?.click()}>Choose files</button>
        <input ref={input} type="file" multiple accept=".pdf,.docx,.txt" hidden onChange={(e) => send(e.target.files)} />
      </div>

      {problems.length > 0 && (
        <ul className="problems" role="alert">
          {problems.map((p, i) => (
            <li key={i}><b>{p.filename}</b>: {p.error}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
