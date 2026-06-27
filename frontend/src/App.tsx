import { useEffect, useRef, useState } from "react";
import { AptitudeProfileDisplay } from "./components/AptitudeProfileDisplay";
import { OccupationMatchesDisplay } from "./components/OccupationMatchesDisplay";
import { RoleFamilyPlanDisplay } from "./components/RoleFamilyPlanDisplay";
import {
  defaultConstraints,
  OptionalConstraints,
} from "./components/OptionalConstraints";
import { PipelineActions } from "./components/PipelineActions";
import {
  defaultResumeInput,
  hasResumeInput,
  ResumeInput,
} from "./components/ResumeInput";
import { VerifiedMatchesDisplay } from "./components/VerifiedMatchesDisplay";
import { usePipeline } from "./hooks/usePipeline";
import { useTheme } from "./hooks/useTheme";

function ProgressLog({
  messages,
  loading,
}: {
  messages: string[];
  loading: boolean;
}) {
  const listRef = useRef<HTMLOListElement>(null);

  useEffect(() => {
    const lastItem = listRef.current?.lastElementChild;
    lastItem?.scrollIntoView({ block: "nearest" });
  }, [messages]);

  if (messages.length === 0) return null;
  return (
    <details className="collapsible-section progress-log" open>
      <summary>Pipeline progress</summary>
      <ol
        ref={listRef}
        className="progress-log-list"
        aria-live="polite"
        aria-busy={loading}
      >
        {messages.map((message, index) => (
          <li key={`${index}-${message}`}>{message}</li>
        ))}
      </ol>
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
  const [resumeInput, setResumeInput] = useState(defaultResumeInput);
  const [constraints, setConstraints] = useState(defaultConstraints);
  const {
    loading,
    error,
    setError,
    progressMessages,
    result,
    runPipeline,
  } = usePipeline();

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
      <ul className="subtitle">
        <li>Upload resume file, or copy/paste.</li>
        <li>Click &apos;Go&apos;.</li>
        <li>
          LLMs assess aptitudes from your resume; O*NET matching and a role
          family plan guide job search.
        </li>
      </ul>

      <ResumeInput
        value={resumeInput}
        onChange={setResumeInput}
        onError={setError}
      />

      <OptionalConstraints
        constraints={constraints}
        onChange={setConstraints}
      />

      <PipelineActions
        loading={loading}
        canRun={hasResumeInput(resumeInput)}
        onRun={() => void runPipeline(resumeInput, constraints)}
      />

      {error && <p className="error">{error}</p>}

      {(loading || progressMessages.length > 0) && (
        <ProgressLog messages={progressMessages} loading={loading} />
      )}

      {result && (
        <>
          <AptitudeProfileDisplay profile={result.aptitude_profile} />
          <OccupationMatchesDisplay matches={result.occupation_matches} />
          <RoleFamilyPlanDisplay plan={result.role_family_plan} />
          <VerifiedMatchesDisplay matches={result.verified_matches} />
        </>
      )}
    </>
  );
}
