import { useEffect, useState } from "react";
import { AptitudeProfileDisplay } from "./components/AptitudeProfileDisplay";
import { InferenceConfidenceDisplay } from "./components/InferenceConfidenceDisplay";
import { OccupationMatchesDisplay } from "./components/OccupationMatchesDisplay";
import { RoleFamilyPlanDisplay } from "./components/RoleFamilyPlanDisplay";
import {
  defaultConstraints,
  // OptionalConstraints,
} from "./components/OptionalConstraints";
import { PipelineActions } from "./components/PipelineActions";
import {
  defaultResumeInput,
  hasResumeInput,
  ResumeInput,
} from "./components/ResumeInput";
import { VerifiedMatchesDisplay } from "./components/VerifiedMatchesDisplay";
import type { StageNavProps } from "./components/SaveAsPdfToolbar";
import { usePipeline } from "./hooks/usePipeline";
import { useTheme } from "./hooks/useTheme";

type AppView =
  | "input"
  | "running"
  | "stage1"
  | "stage2"
  | "stage3"
  | "stage4"
  | "stage5";

function StageBottomNav({ stageNav }: { stageNav: StageNavProps }) {
  const disabled = stageNav.disabled ?? false;
  return (
    <div className="actions step-nav step-nav-end">
        {!stageNav.hideBack && (
          <button
            type="button"
            className="back"
            disabled={disabled}
            onClick={stageNav.onBack}
          >
            Back
          </button>
        )}
        {stageNav.isLastStage ? (
          <button
            type="button"
            className="secondary success"
            disabled={disabled}
            onClick={stageNav.onStartOver}
          >
            Start over
          </button>
        ) : (
          <button type="button" disabled={disabled} onClick={stageNav.onNext}>
            Next
          </button>
        )}
    </div>
  );
}

function ProgressLog({
  messages,
  loading,
}: {
  messages: string[];
  loading: boolean;
}) {
  return (
    <details className="collapsible-section progress-log" open>
      <summary>Pipeline progress</summary>
      <ol
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
  // const [constraints, setConstraints] = useState(defaultConstraints);
  const [view, setView] = useState<AppView>("input");
  const [stepNavDisabled, setStepNavDisabled] = useState(false);
  const {
    loading,
    error,
    setError,
    progressMessages,
    result,
    runPipeline,
    resetPipeline,
  } = usePipeline();

  useEffect(() => {
    if (loading) {
      setView("running");
    }
  }, [loading]);

  useEffect(() => {
    if (result) {
      setView("stage1");
    }
  }, [result]);

  useEffect(() => {
    if (!loading && error && !result) {
      setView("input");
    }
  }, [loading, error, result]);

  useEffect(() => {
    setStepNavDisabled(false);
  }, [view]);

  function handleStartOver() {
    resetPipeline();
    setView("input");
  }

  function goToPreviousResultStage() {
    setView((current) => {
      if (current === "stage1") return "running";
      if (current === "stage2") return "stage1";
      if (current === "stage3") return "stage2";
      if (current === "stage4") return "stage3";
      if (current === "stage5") return "stage4";
      return current;
    });
  }

  function goToNextResultStage() {
    setView((current) => {
      if (current === "stage1") return "stage2";
      if (current === "stage2") return "stage3";
      if (current === "stage3") return "stage4";
      if (current === "stage4") return "stage5";
      return current;
    });
  }

  function withStepNavDisabled(nav: StageNavProps): StageNavProps {
    return { ...nav, disabled: stepNavDisabled };
  }

  const stage1Nav: StageNavProps = {
    onBack: goToPreviousResultStage,
    onNext: goToNextResultStage,
    onStartOver: handleStartOver,
    isLastStage: false,
  };

  const stage2Nav: StageNavProps = {
    onBack: goToPreviousResultStage,
    onNext: goToNextResultStage,
    onStartOver: handleStartOver,
    isLastStage: false,
  };

  const stage3Nav: StageNavProps = {
    onBack: goToPreviousResultStage,
    onNext: goToNextResultStage,
    onStartOver: handleStartOver,
    isLastStage: false,
  };

  const stage4Nav: StageNavProps = {
    onBack: goToPreviousResultStage,
    onNext: goToNextResultStage,
    onStartOver: handleStartOver,
    isLastStage: false,
  };

  const stage5Nav: StageNavProps = {
    onBack: goToPreviousResultStage,
    onNext: goToNextResultStage,
    onStartOver: handleStartOver,
    isLastStage: true,
  };

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

      <div className="step-panel" hidden={view !== "input"}>
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

        {/*
        <OptionalConstraints
          constraints={constraints}
          onChange={setConstraints}
        />
        */}

        <PipelineActions
          loading={loading}
          canRun={hasResumeInput(resumeInput)}
          onRun={() => void runPipeline(resumeInput, defaultConstraints)}
        />

        {error && <p className="error">{error}</p>}
      </div>

      <div className="step-panel" hidden={view !== "running"}>
        <p className="step-label">Running pipeline</p>
        {progressMessages.length > 0 ? (
          <ProgressLog messages={progressMessages} loading={loading} />
        ) : (
          <p className="running-status" aria-live="polite">
            Starting pipeline…
          </p>
        )}
        {error && <p className="error">{error}</p>}
        {result && !loading && (
          <div className="actions step-nav step-nav-end">
            <button type="button" onClick={() => setView("stage1")}>
              Next
            </button>
          </div>
        )}
      </div>

      {result && (
        <>
          <div className="step-panel" hidden={view !== "stage1"}>
            <AptitudeProfileDisplay
              profile={result.aptitude_profile}
              stageNav={withStepNavDisabled(stage1Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage1Nav)} />
          </div>

          <div className="step-panel" hidden={view !== "stage2"}>
            <InferenceConfidenceDisplay
              profile={result.aptitude_profile}
              stageNav={withStepNavDisabled(stage2Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage2Nav)} />
          </div>

          <div className="step-panel" hidden={view !== "stage3"}>
            <OccupationMatchesDisplay
              matches={result.occupation_matches}
              stageNav={withStepNavDisabled(stage3Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage3Nav)} />
          </div>

          <div className="step-panel" hidden={view !== "stage4"}>
            <RoleFamilyPlanDisplay
              plan={result.role_family_plan}
              stageNav={withStepNavDisabled(stage4Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage4Nav)} />
          </div>

          <div className="step-panel" hidden={view !== "stage5"}>
            <VerifiedMatchesDisplay
              matches={result.verified_matches}
              stageNav={withStepNavDisabled(stage5Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage5Nav)} />
          </div>
        </>
      )}
    </>
  );
}
