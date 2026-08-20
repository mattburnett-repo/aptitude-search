import { useEffect, useState } from "react";
import { AptitudeProfileDisplay } from "./components/AptitudeProfileDisplay";
import { InferenceConfidenceDisplay } from "./components/InferenceConfidenceDisplay";
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
import {
  InputHero,
  InputTrustNotes,
  SiteFooter,
  SiteHeader,
  SiteShell,
} from "./components/SiteChrome";
import type { StageNavProps } from "./components/SaveAsPdfToolbar";
import { usePipeline } from "./hooks/usePipeline";
import { useTheme } from "./hooks/useTheme";

type AppView =
  | "input"
  | "constraints"
  | "running"
  | "stage1"
  | "stage2"
  | "stage3"
  | "stage4"
  | "stage5";

const RESULT_STEPS = [
  { id: "constraints" as const, label: "Criteria" },
  { id: "stage1" as const, label: "Profile" },
  { id: "stage2" as const, label: "Confidence" },
  { id: "stage3" as const, label: "Matches" },
  { id: "stage4" as const, label: "Roles" },
  { id: "stage5" as const, label: "Jobs" },
];

const PIPELINE_STAGE_COUNT = 3;

function parsePipelineStage(message: string): number | null {
  const match = /Stage\s+(\d+)/i.exec(message);
  return match ? Number(match[1]) : null;
}

function formatRunningLabel(messages: string[]): string {
  if (messages.length === 0) {
    return "Starting pipeline…";
  }

  const latest = messages[messages.length - 1]!;
  if (latest.toLowerCase().includes("pipeline complete")) {
    return "Pipeline complete";
  }

  const stageFromLatest = parsePipelineStage(latest);
  const stage =
    stageFromLatest ??
    [...messages].reverse().map(parsePipelineStage).find((value) => value != null) ??
    1;

  const detail = latest
    .replace(/^Stage\s+\d+:?\s*/i, "")
    .replace(/\.$/, "")
    .trim();

  if (detail && !/^Stage\s+\d+/i.test(latest)) {
    return `Stage ${stage} of ${PIPELINE_STAGE_COUNT} — ${detail}`;
  }

  if (detail) {
    return `Stage ${stage} of ${PIPELINE_STAGE_COUNT} — ${detail}`;
  }

  return `Stage ${stage} of ${PIPELINE_STAGE_COUNT}`;
}

function progressItemClassName(
  index: number,
  messages: string[],
  loading: boolean,
): string | undefined {
  const isLast = index === messages.length - 1;
  if (isLast && loading) return "progress-log-item-active";
  if (!isLast || !loading) return "progress-log-item-complete";
  return undefined;
}

const STAGE_HERO: Partial<
  Record<AppView, { title: string; lead: string }>
> = {
  constraints: {
    title: "Optional search criteria",
    lead: "Narrow job discovery by location, remote preference, salary, or industries. All fields are optional.",
  },
  running: {
    title: "Running your analysis",
    lead: "Assessing aptitudes, matching careers, and searching open roles.",
  },
  stage1: {
    title: "Your aptitude profile",
    lead: "Skills, strengths, working style, culture preferences, and interests from your resume.",
  },
  stage2: {
    title: "How sure we are",
    lead: "Confidence levels for each inference in your profile.",
  },
  stage3: {
    title: "Matching careers",
    lead: "Careers ranked by fit to your aptitude profile.",
  },
  stage4: {
    title: "Job types to try",
    lead: "Broad job types that fit how you work — and the titles we’ll search for.",
  },
  stage5: {
    title: "Job search results",
    lead: "Verified postings discovered from your profile and job types to try.",
  },
};

function StepSectionHero({ view }: { view: AppView }) {
  const hero = STAGE_HERO[view];
  if (!hero) return null;

  return (
    <header className="step-section-hero">
      <h2 className="step-section-hero-title">{hero.title}</h2>
      <p className="step-section-hero-lead">{hero.lead}</p>
    </header>
  );
}

function resultStepIndex(view: AppView): number {
  if (view === "constraints") return 0;
  if (view.startsWith("stage")) return Number(view.replace("stage", ""));
  return -1;
}

function StepIndicator({
  view,
  hasResult,
  navDisabled,
  onStepSelect,
}: {
  view: AppView;
  hasResult: boolean;
  navDisabled: boolean;
  onStepSelect: (step: AppView) => void;
}) {
  if (view === "input") return null;

  const canNavigate = hasResult && !navDisabled;

  return (
    <nav className="step-indicator" aria-label="Pipeline steps">
      <div className="step-indicator-inner">
        <ol className="step-indicator-list">
        {RESULT_STEPS.map((step, index) => {
          const isActive = view === step.id;
          const isRunning =
            view === "running" && index === 1 && !hasResult;
          const stepIndex = resultStepIndex(view);
          const isComplete = hasResult && stepIndex > index;

          return (
            <li key={step.id}>
              <button
                type="button"
                className={[
                  "step-indicator-item",
                  isActive ? "step-indicator-item-active" : "",
                  isRunning ? "step-indicator-item-running" : "",
                  isComplete ? "step-indicator-item-complete" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                disabled={!canNavigate}
                aria-current={isActive ? "step" : undefined}
                onClick={() => onStepSelect(step.id)}
              >
                <span className="step-indicator-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="step-indicator-label">{step.label}</span>
              </button>
            </li>
          );
        })}
        </ol>
      </div>
    </nav>
  );
}

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
          <button
            type="button"
            className="primary-cta"
            disabled={disabled}
            onClick={stageNav.onNext}
          >
            Next →
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
          <li
            key={`${index}-${message}`}
            className={progressItemClassName(index, messages, loading)}
          >
            {message}
          </li>
        ))}
      </ol>
    </details>
  );
}

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [resumeInput, setResumeInput] = useState(defaultResumeInput);
  const [constraints, setConstraints] = useState(defaultConstraints);
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
      setView("constraints");
    }
  }, [loading, error, result]);

  useEffect(() => {
    setStepNavDisabled(false);
  }, [view]);

  function handleStartOver() {
    resetPipeline();
    setConstraints(defaultConstraints);
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

  const siteMode =
    view === "input" || view === "constraints" || view === "running"
      ? "marketing"
      : "tool";

  return (
    <SiteShell mode={siteMode}>
      <div className="site-top-chrome">
        <SiteHeader theme={theme} onToggleTheme={toggleTheme} />
        <StepIndicator
          view={view}
          hasResult={Boolean(result)}
          navDisabled={stepNavDisabled}
          onStepSelect={setView}
        />
      </div>

      <main className="site-main">
        <div className="site-content">
          <div className="step-panel" hidden={view !== "input"}>
            <InputHero />

            <ol className="input-steps" aria-label="How it works">
          <li>
            <span className="input-step-number">01</span>
            <span className="input-step-text">
              Upload a resume file or paste your text.
            </span>
          </li>
          <li>
            <span className="input-step-number">02</span>
            <span className="input-step-text">
              Add optional search criteria such as location or remote preference.
            </span>
          </li>
          <li>
            <span className="input-step-number">03</span>
            <span className="input-step-text">
              Run the pipeline to assess aptitudes and match roles.
            </span>
          </li>
          <li>
            <span className="input-step-number">04</span>
            <span className="input-step-text">
              Review your profile, matches, and verified job postings.
            </span>
          </li>
        </ol>

        <div className="input-panel">
          <ResumeInput
            value={resumeInput}
            onChange={setResumeInput}
            onError={setError}
          />

          <PipelineActions
            loading={loading}
            canRun={hasResumeInput(resumeInput)}
            onRun={() => {
              setError(null);
              setView("constraints");
            }}
          />

          {error && <p className="error">{error}</p>}
        </div>

        <InputTrustNotes />
          </div>

          <div className="step-panel" hidden={view !== "constraints"}>
            <StepSectionHero view="constraints" />

            <OptionalConstraints
              constraints={constraints}
              onChange={setConstraints}
              layout="panel"
            />

            <div className="actions step-nav step-nav-end">
              <button
                type="button"
                className="back"
                disabled={loading}
                onClick={() => setView("input")}
              >
                Back
              </button>
              <PipelineActions
                loading={loading}
                canRun={hasResumeInput(resumeInput)}
                inline
                onRun={() => void runPipeline(resumeInput, constraints)}
              />
            </div>

            {error && <p className="error">{error}</p>}
          </div>

          <div className="step-panel" hidden={view !== "running"}>
            <StepSectionHero view="running" />
        <p className="running-stage-label" aria-live="polite">
          {loading && (
            <span className="running-spinner" aria-hidden="true" />
          )}
          {formatRunningLabel(progressMessages)}
        </p>
        {progressMessages.length > 0 && (
          <ProgressLog messages={progressMessages} loading={loading} />
        )}
        {error && <p className="error">{error}</p>}
        {result && !loading && (
          <div className="actions step-nav step-nav-end">
            <button
              type="button"
              className="primary-cta"
              onClick={() => setView("stage1")}
            >
              Next →
            </button>
          </div>
        )}
          </div>

          {result && (
            <>
              <div className="step-panel" hidden={view !== "stage1"}>
                <StepSectionHero view="stage1" />
            <AptitudeProfileDisplay
              profile={result.aptitude_profile}
              stageNav={withStepNavDisabled(stage1Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage1Nav)} />
              </div>

              <div className="step-panel" hidden={view !== "stage2"}>
                <StepSectionHero view="stage2" />
            <InferenceConfidenceDisplay
              profile={result.aptitude_profile}
              stageNav={withStepNavDisabled(stage2Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage2Nav)} />
              </div>

              <div className="step-panel" hidden={view !== "stage3"}>
                <StepSectionHero view="stage3" />
            <OccupationMatchesDisplay
              matches={result.occupation_matches}
              stageNav={withStepNavDisabled(stage3Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage3Nav)} />
              </div>

              <div className="step-panel" hidden={view !== "stage4"}>
                <StepSectionHero view="stage4" />
            <RoleFamilyPlanDisplay
              plan={result.role_family_plan}
              stageNav={withStepNavDisabled(stage4Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage4Nav)} />
              </div>

              <div className="step-panel" hidden={view !== "stage5"}>
                <StepSectionHero view="stage5" />
            <VerifiedMatchesDisplay
              matches={result.verified_matches}
              stageNav={withStepNavDisabled(stage5Nav)}
              onPdfBusyChange={setStepNavDisabled}
            />
            <StageBottomNav stageNav={withStepNavDisabled(stage5Nav)} />
              </div>
            </>
          )}
        </div>
      </main>

      <SiteFooter />
    </SiteShell>
  );
}
