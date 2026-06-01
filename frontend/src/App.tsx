import { useState } from "react";

const API_BASE = "/api";

type PipelineResult = {
  aptitude_profile: unknown;
  verified_matches: unknown;
};

type Constraints = {
  location: string;
  remote_preference: string;
  salary_min: string;
  industries_include: string;
  industries_exclude: string;
};

const defaultConstraints: Constraints = {
  location: "",
  remote_preference: "any",
  salary_min: "",
  industries_include: "",
  industries_exclude: "",
};

function StageJsonPanel({ title, data }: { title: string; data: unknown }) {
  if (!data) return null;
  return (
    <details className="stage" open>
      <summary>{title}</summary>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </details>
  );
}

export default function App() {
  const [resume, setResume] = useState("");
  const [constraints, setConstraints] = useState(defaultConstraints);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PipelineResult | null>(null);

  function buildConstraintsBody() {
    return {
      location: constraints.location,
      remote_preference: constraints.remote_preference,
      salary_min: constraints.salary_min ? Number(constraints.salary_min) : null,
      industries_include: constraints.industries_include
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      industries_exclude: constraints.industries_exclude
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };
  }

  async function apiFetch(path: string, body: unknown) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      const msg =
        typeof data.detail === "string"
          ? data.detail
          : (data.error ?? res.statusText);
      throw new Error(msg);
    }
    return data;
  }

  async function runPipeline() {
    setError(null);
    setLoading(true);
    try {
      const data = await apiFetch("/v1/pipeline", {
        resume,
        constraints: buildConstraintsBody(),
      });
      setResult(data as PipelineResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  function exportJson() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "aptitude-search-results.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function copyVerified() {
    if (!result?.verified_matches) return;
    void navigator.clipboard.writeText(
      JSON.stringify(result.verified_matches, null, 2)
    );
  }

  return (
    <>
      <h1>Aptitude Search</h1>
      <p className="subtitle">
        Run pipeline: resume → aptitude profile → job search (verified matches).
        LLM is configured on the API server (config.toml).
      </p>

      <section>
        <label htmlFor="resume">Resume (plain text)</label>
        <textarea
          id="resume"
          value={resume}
          onChange={(e) => setResume(e.target.value)}
          placeholder="Paste resume text..."
        />
      </section>

      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>
          Optional constraints (Prompt 2)
        </h2>
        <div className="grid grid-2">
          <div>
            <label htmlFor="location">Location</label>
            <input
              id="location"
              value={constraints.location}
              onChange={(e) =>
                setConstraints({ ...constraints, location: e.target.value })
              }
            />
          </div>
          <div>
            <label htmlFor="remote">Remote preference</label>
            <select
              id="remote"
              value={constraints.remote_preference}
              onChange={(e) =>
                setConstraints({
                  ...constraints,
                  remote_preference: e.target.value,
                })
              }
            >
              <option value="any">any</option>
              <option value="remote">remote</option>
              <option value="hybrid">hybrid</option>
              <option value="onsite">onsite</option>
            </select>
          </div>
          <div>
            <label htmlFor="salary">Salary min</label>
            <input
              id="salary"
              type="text"
              value={constraints.salary_min}
              onChange={(e) =>
                setConstraints({ ...constraints, salary_min: e.target.value })
              }
            />
          </div>
          <div>
            <label htmlFor="include">Industries include (comma-separated)</label>
            <input
              id="include"
              value={constraints.industries_include}
              onChange={(e) =>
                setConstraints({
                  ...constraints,
                  industries_include: e.target.value,
                })
              }
            />
          </div>
          <div>
            <label htmlFor="exclude">Industries exclude (comma-separated)</label>
            <input
              id="exclude"
              value={constraints.industries_exclude}
              onChange={(e) =>
                setConstraints({
                  ...constraints,
                  industries_exclude: e.target.value,
                })
              }
            />
          </div>
        </div>
      </section>

      <div className="actions">
        <button
          type="button"
          disabled={loading || !resume.trim()}
          onClick={runPipeline}
        >
          {loading ? "Running pipeline…" : "Run pipeline (1 → 2)"}
        </button>
        {result && (
          <>
            <button type="button" className="secondary" onClick={exportJson}>
              Export JSON
            </button>
            {result.verified_matches && (
              <button type="button" className="secondary" onClick={copyVerified}>
                Copy verified matches
              </button>
            )}
          </>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          <StageJsonPanel
            title="Stage 1 — Aptitude profile"
            data={result.aptitude_profile}
          />
          <StageJsonPanel
            title="Stage 2 — Verified matches"
            data={result.verified_matches}
          />
        </>
      )}
    </>
  );
}
