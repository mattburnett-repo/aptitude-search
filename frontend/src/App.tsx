import { useEffect, useState } from "react";

const API_BASE = "/api";
const STORAGE_KEY = "aptitude-search-openai-key";
const MODEL_KEY = "aptitude-search-openai-model";

type PipelineResult = {
  aptitude_profile: unknown;
  targeting_strategy: unknown;
  search_queries: unknown;
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

function StagePanel({ title, data }: { title: string; data: unknown }) {
  if (!data) return null;
  return (
    <details className="stage" open>
      <summary>{title}</summary>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </details>
  );
}

export default function App() {
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [resume, setResume] = useState("");
  const [constraints, setConstraints] = useState(defaultConstraints);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [corrections, setCorrections] = useState("");
  const [regenStage, setRegenStage] = useState<"2" | "3">("2");

  useEffect(() => {
    setApiKey(localStorage.getItem(STORAGE_KEY) ?? "");
    setModel(localStorage.getItem(MODEL_KEY) ?? "gpt-4o");
  }, []);

  useEffect(() => {
    if (apiKey) localStorage.setItem(STORAGE_KEY, apiKey);
  }, [apiKey]);

  useEffect(() => {
    localStorage.setItem(MODEL_KEY, model);
  }, [model]);

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
      headers: {
        "Content-Type": "application/json",
        "X-OpenAI-Api-Key": apiKey,
        "X-OpenAI-Model": model,
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error ?? res.statusText);
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
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function runIterate() {
    if (!result) return;
    setError(null);
    setLoading(true);
    try {
      const data = await apiFetch("/v1/iterate", {
        regenerate_from_stage: Number(regenStage),
        current_artifacts: {
          aptitude_profile: result.aptitude_profile,
          targeting_strategy: result.targeting_strategy,
          search_queries: result.search_queries,
        },
        user_corrections: corrections,
        constraints: buildConstraintsBody(),
      });
      setResult((prev) =>
        prev
          ? {
              aptitude_profile: prev.aptitude_profile,
              targeting_strategy:
                (data.targeting_strategy as unknown) ?? prev.targeting_strategy,
              search_queries:
                (data.search_queries as unknown) ?? prev.search_queries,
            }
          : null
      );
      setCorrections("");
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

  return (
    <>
      <h1>Aptitude Search</h1>
      <p className="subtitle">
        Career inference before search. API key stays in your browser only.
      </p>

      <section className="grid grid-2">
        <div>
          <label htmlFor="apiKey">OpenAI API key</label>
          <input
            id="apiKey"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-..."
            autoComplete="off"
          />
        </div>
        <div>
          <label htmlFor="model">Model</label>
          <input
            id="model"
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          />
        </div>
      </section>

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
          Optional constraints
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
          disabled={loading || !apiKey || !resume.trim()}
          onClick={runPipeline}
        >
          {loading ? "Running pipeline…" : "Run pipeline"}
        </button>
        {result && (
          <button type="button" className="secondary" onClick={exportJson}>
            Export JSON
          </button>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          <StagePanel title="Stage 1 — Aptitude profile" data={result.aptitude_profile} />
          <StagePanel title="Stage 2 — Targeting strategy" data={result.targeting_strategy} />
          <StagePanel title="Stage 3 — Search queries" data={result.search_queries} />

          <section className="refine">
            <h2 style={{ fontSize: "1rem" }}>Refine (Prompt 4)</h2>
            <label htmlFor="regen">Regenerate from stage</label>
            <select
              id="regen"
              value={regenStage}
              onChange={(e) => setRegenStage(e.target.value as "2" | "3")}
            >
              <option value="2">2 — strategy + queries</option>
              <option value="3">3 — queries only</option>
            </select>
            <label htmlFor="corrections" style={{ marginTop: "0.75rem" }}>
              Your corrections
            </label>
            <textarea
              id="corrections"
              value={corrections}
              onChange={(e) => setCorrections(e.target.value)}
              placeholder="e.g. Target staff platform roles, remote only, add healthcare SaaS…"
            />
            <div className="actions">
              <button
                type="button"
                disabled={loading || !corrections.trim()}
                onClick={runIterate}
              >
                Apply corrections
              </button>
            </div>
          </section>
        </>
      )}
    </>
  );
}
