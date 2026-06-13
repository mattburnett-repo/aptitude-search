import { useRef, useState } from "react";
import { runPipelineStream, type PipelineResult } from "./pipelineStream";
import { readFileAsBase64 } from "./readFileAsBase64";
import {
  isPdfResumeFile,
  isSupportedResumeFile,
  isTextResumeFile,
} from "./resumeUpload";
import { useTheme } from "./useTheme";

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

function ProgressLog({ messages }: { messages: string[] }) {
  if (messages.length === 0) return null;
  return (
    <section className="progress-log" aria-live="polite" aria-busy="true">
      <h2 className="progress-log-title">Pipeline progress</h2>
      <ol className="progress-log-list">
        {messages.map((message, index) => (
          <li key={`${index}-${message}`}>{message}</li>
        ))}
      </ol>
    </section>
  );
}

function StageJsonPanel({ title, data }: { title: string; data: unknown }) {
  if (!data) return null;
  return (
    <details className="stage" open>
      <summary>{title}</summary>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </details>
  );
}

function ThemeToggleIcon({ theme }: { theme: "light" | "dark" }) {
  if (theme === "light") {
    return (
      <svg
        aria-hidden="true"
        className="theme-toggle-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    );
  }

  return (
    <svg
      aria-hidden="true"
      className="theme-toggle-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const resumeFileInputRef = useRef<HTMLInputElement>(null);
  const [resume, setResume] = useState("");
  const [resumePdfFile, setResumePdfFile] = useState<File | null>(null); // PDF only; not read client-side
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [constraints, setConstraints] = useState(defaultConstraints);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
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

  async function runPipeline() {
    setError(null);
    setResult(null);
    setProgressMessages([]);
    setLoading(true);
    try {
      // PDF: base64 in JSON (resume_pdf_base64). Text: plain resume string.
      const body = resumePdfFile
        ? {
            resume: "",
            resume_pdf_base64: await readFileAsBase64(resumePdfFile),
            constraints: buildConstraintsBody(),
          }
        : {
            resume,
            constraints: buildConstraintsBody(),
          };
      const data = await runPipelineStream(body, (message) => {
        setProgressMessages((prev) => [...prev, message]);
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  function hasResumeInput() {
    return Boolean(resume.trim() || resumePdfFile);
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

  async function handleResumeFileSelect(file: File) {
    if (!isSupportedResumeFile(file)) {
      setError("Please choose a .txt, .md, or .pdf resume file.");
      return;
    }

    if (isPdfResumeFile(file)) {
      // Keep the File in memory; backend extracts text via pypdf.
      setResumePdfFile(file);
      setResume("");
      setResumeFileName(file.name);
      setError(null);
      return;
    }

    if (!isTextResumeFile(file)) {
      setError("Please choose a .txt, .md, or .pdf resume file.");
      return;
    }

    try {
      // Plain text: read here and send as resume string.
      const text = await file.text();
      setResumePdfFile(null);
      setResume(text);
      setResumeFileName(file.name);
      setError(null);
    } catch {
      setError("Could not read the selected file.");
    }
  }

  function clearResumeFile() {
    setResumePdfFile(null);
    setResumeFileName(null);
    setResume("");
  }

  function handleResumeFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) void handleResumeFileSelect(file);
    event.target.value = "";
  }

  function handleResumeChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    setResume(event.target.value);
    setResumePdfFile(null);
    setResumeFileName(null);
  }

  return (
    <>
      <div className="page-header">
        <h1>Aptitude Search</h1>
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          <ThemeToggleIcon theme={theme} />
        </button>
      </div>
      <p className="subtitle">
        Run pipeline: resume → aptitude profile → job search (verified matches).
        LLM is configured on the API server (config.toml).
      </p>

      <section>
        <label htmlFor="resume">Resume</label>
        <div className="resume-toolbar">
          <input
            ref={resumeFileInputRef}
            id="resume-file"
            type="file"
            accept=".txt,.md,.text,.pdf,text/plain,application/pdf"
            className="resume-file-input"
            onChange={handleResumeFileChange}
          />
          <button
            type="button"
            className="secondary resume-file-button"
            onClick={() => resumeFileInputRef.current?.click()}
          >
            Choose file
          </button>
          {resumeFileName && (
            <span className="resume-file-name">{resumeFileName}</span>
          )}
          {resumePdfFile && (
            <button
              type="button"
              className="secondary resume-file-button"
              onClick={clearResumeFile}
            >
              Clear file
            </button>
          )}
        </div>
        <textarea
          id="resume"
          value={resume}
          onChange={handleResumeChange}
          readOnly={Boolean(resumePdfFile)}
          placeholder={
            resumePdfFile
              ? "PDF resume attached. Text will be extracted on the server when you run the pipeline."
              : "Paste resume text or choose a file..."
          }
        />
      </section>

      <section>
        <h2 style={{ fontSize: "1rem", marginBottom: "0.75rem" }}>
          Optional constraints
        </h2>
        <div className="grid grid-3">
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
              value={constraints.salary_min}
              onChange={(e) =>
                setConstraints({ ...constraints, salary_min: e.target.value })
              }
            />
          </div>
        </div>
        <div className="grid grid-2">
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
          disabled={loading || !hasResumeInput()}
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

      {(loading || progressMessages.length > 0) && (
        <ProgressLog messages={progressMessages} />
      )}

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
