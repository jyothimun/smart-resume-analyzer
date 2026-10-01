const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(BASE + path, options);
  } catch {
    throw new Error("Couldn't reach the backend. Start it with: python app.py (inside the backend folder).");
  }
  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const body = isJson ? await res.json() : null;
  if (!res.ok) {
    const err = new Error(body?.error || `Request failed (${res.status})`);
    err.body = body;
    throw err;
  }
  return body;
}

const json = (method, data) => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

export const api = {
  health: () => request("/api/health"),
  listJobs: () => request("/api/jobs"),
  getJob: (id) => request(`/api/jobs/${id}`),
  createJob: (data) => request("/api/jobs", json("POST", data)),
  deleteJob: (id) => request(`/api/jobs/${id}`, { method: "DELETE" }),
  uploadResumes: (id, files) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return request(`/api/jobs/${id}/resumes`, { method: "POST", body: form });
  },
  getCandidate: (id) => request(`/api/candidates/${id}`),
  deleteCandidate: (id) => request(`/api/candidates/${id}`, { method: "DELETE" }),
  insights: (id) => request(`/api/candidates/${id}/insights`, { method: "POST" }),
  loadDemo: () => request("/api/demo", { method: "POST" }),
  exportUrl: (id) => `${BASE}/api/jobs/${id}/export.csv`,
};
