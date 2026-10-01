import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import Sidebar from "./components/Sidebar.jsx";
import JobView from "./components/JobView.jsx";
import JobForm from "./components/JobForm.jsx";
import CandidateDrawer from "./components/CandidateDrawer.jsx";
import EmptyState from "./components/EmptyState.jsx";

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [job, setJob] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [health, setHealth] = useState(null); // null = checking, false = offline
  const [toast, setToast] = useState(null);
  const [loaded, setLoaded] = useState(false);

  const notify = useCallback((message, kind = "info") => {
    setToast({ message, kind, id: Date.now() });
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(t);
  }, [toast]);

  const refreshJobs = useCallback(async () => {
    const list = await api.listJobs();
    setJobs(list);
    return list;
  }, []);

  const refreshJob = useCallback(async (id) => {
    const data = await api.getJob(id);
    setJob(data);
  }, []);

  // first load: backend health + jobs
  useEffect(() => {
    (async () => {
      try {
        setHealth(await api.health());
        const list = await refreshJobs();
        if (list.length) setActiveId(list[0].id);
      } catch (e) {
        setHealth(false);
        notify(e.message, "error");
      } finally {
        setLoaded(true);
      }
    })();
  }, [refreshJobs, notify]);

  useEffect(() => {
    if (activeId == null) {
      setJob(null);
      return;
    }
    setSelectedId(null);
    refreshJob(activeId).catch((e) => notify(e.message, "error"));
  }, [activeId, refreshJob, notify]);

  const afterChange = useCallback(async () => {
    await Promise.all([refreshJobs(), activeId != null ? refreshJob(activeId) : null]);
  }, [refreshJobs, refreshJob, activeId]);

  async function handleCreate(data) {
    const created = await api.createJob(data);
    await refreshJobs();
    setActiveId(created.id);
    setShowForm(false);
    notify(`Created “${created.title}”. Now drop some resumes in.`);
  }

  async function handleDeleteJob(id) {
    if (!window.confirm("Delete this job and all its screened resumes?")) return;
    try {
      await api.deleteJob(id);
      const list = await refreshJobs();
      setActiveId(list.length ? list[0].id : null);
      notify("Job deleted.");
    } catch (e) {
      notify(e.message, "error");
    }
  }

  async function handleDemo() {
    try {
      const created = await api.loadDemo();
      await refreshJobs();
      setActiveId(created.id);
      notify("Demo loaded: one job, six resumes, already ranked.");
    } catch (e) {
      notify(e.message, "error");
    }
  }

  const offline = health === false;

  return (
    <div className="shell">
      <Sidebar
        jobs={jobs}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={() => setShowForm(true)}
        health={health}
      />

      <main className="main">
        {offline && (
          <div className="banner" role="alert">
            Couldn't reach the backend. Open a terminal in the <b>backend</b> folder and run <code>python app.py</code>,
            then refresh this page.
          </div>
        )}

        {loaded && !offline && !job && (
          <EmptyState hasJobs={jobs.length > 0} onNew={() => setShowForm(true)} onDemo={handleDemo} />
        )}

        {job && (
          <JobView
            job={job}
            onChanged={afterChange}
            onOpen={setSelectedId}
            onDelete={() => handleDeleteJob(job.id)}
            notify={notify}
          />
        )}
      </main>

      {selectedId != null && (
        <CandidateDrawer
          candidateId={selectedId}
          onClose={() => setSelectedId(null)}
          onDeleted={async () => {
            setSelectedId(null);
            await afterChange();
            notify("Candidate removed.");
          }}
          notify={notify}
          aiEnabled={!!health?.ai_enabled}
        />
      )}

      {showForm && <JobForm onClose={() => setShowForm(false)} onCreate={handleCreate} />}

      {toast && (
        <div className={`toast ${toast.kind}`} role="status" key={toast.id}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
