import { useRef } from "react";
import { SaveAsPdfToolbar, type StageNavProps } from "./SaveAsPdfToolbar";

type Confidence = "high" | "medium" | "low";

type JobPosting = {
  company: string;
  role: string;
  url: string;
  match_description: string;
  location?: string;
  employment_type?: string;
  seniority_level?: string;
  match_signals?: string[];
  confidence?: Confidence;
};

export type VerifiedMatches = {
  search_plan: string[];
  results: JobPosting[];
  notes: string[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isConfidence(value: unknown): value is Confidence {
  return value === "high" || value === "medium" || value === "low";
}

function isVerifiedMatches(value: unknown): value is VerifiedMatches {
  if (!isRecord(value)) return false;
  return (
    Array.isArray(value.search_plan) &&
    Array.isArray(value.results) &&
    Array.isArray(value.notes)
  );
}

function ConfidenceBadge({ level }: { level: Confidence }) {
  return (
    <span className={`confidence-badge confidence-${level}`}>{level}</span>
  );
}

function JobCard({ job }: { job: JobPosting }) {
  const meta = [
    job.location,
    job.employment_type,
    job.seniority_level,
  ].filter(Boolean);

  return (
    <article
      className={[
        "job-card",
        job.confidence === "high" ? "job-card-high-confidence" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <header className="job-card-header">
        <div>
          <h4 className="job-card-role">{job.role}</h4>
          <p className="job-card-company">{job.company}</p>
        </div>
        {job.confidence && isConfidence(job.confidence) && (
          <ConfidenceBadge level={job.confidence} />
        )}
      </header>

      {meta.length > 0 && (
        <p className="job-card-meta">{meta.join(" · ")}</p>
      )}

      <p className="job-card-match">{job.match_description}</p>

      {job.match_signals && job.match_signals.length > 0 && (
        <ul className="job-card-signals">
          {job.match_signals.map((signal) => (
            <li key={signal}>{signal}</li>
          ))}
        </ul>
      )}

      <a
        className="job-card-link"
        href={job.url}
        target="_blank"
        rel="noreferrer noopener"
      >
        View posting
      </a>
    </article>
  );
}

type VerifiedMatchesDisplayProps = {
  matches: unknown;
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
};

function VerifiedSaveAsPdfToolbar({
  matchesRef,
  stageNav,
  onPdfBusyChange,
}: {
  matchesRef: React.RefObject<HTMLDivElement | null>;
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
}) {
  return (
    <SaveAsPdfToolbar
      contentRef={matchesRef}
      stageNav={stageNav}
      onPdfBusyChange={onPdfBusyChange}
      loadExporter={async () => {
        const { openVerifiedMatchesPdf } = await import(
          "../lib/exportVerifiedMatchesPdf"
        );
        return openVerifiedMatchesPdf;
      }}
    />
  );
}

export function VerifiedMatchesDisplay({
  matches,
  stageNav,
  onPdfBusyChange,
}: VerifiedMatchesDisplayProps) {
  const matchesRef = useRef<HTMLDivElement>(null);

  if (!matches) return null;

  if (!isVerifiedMatches(matches)) {
    return (
      <details className="collapsible-section" open>
        <summary>Step 5 — Job search results</summary>
        <VerifiedSaveAsPdfToolbar
          matchesRef={matchesRef}
          stageNav={stageNav}
          onPdfBusyChange={onPdfBusyChange}
        />
        <div ref={matchesRef} className="collapsible-section-body verified-matches">
          <pre className="aptitude-raw-pre">{JSON.stringify(matches, null, 2)}</pre>
        </div>
      </details>
    );
  }

  return (
    <details className="collapsible-section" open>
      <summary>Step 5 — Job search results</summary>
      <VerifiedSaveAsPdfToolbar
        matchesRef={matchesRef}
        stageNav={stageNav}
        onPdfBusyChange={onPdfBusyChange}
      />
      <div className="collapsible-section-body">
        <div ref={matchesRef} className="verified-matches">
          {matches.search_plan.length > 0 && (
            <section className="verified-section">
              <h3 className="verified-section-title">What we looked for</h3>
              <ol className="verified-search-plan">
                {matches.search_plan.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
            </section>
          )}

          <section className="verified-section">
            <h3 className="verified-section-title">
              Results ({matches.results.length})
            </h3>
            {matches.results.length === 0 ? (
              <p className="verified-empty">No verified postings found.</p>
            ) : (
              <div className="job-card-list">
                {matches.results.map((job, index) => (
                  <JobCard
                    key={`${job.company}-${job.role}-${job.url}-${index}`}
                    job={job}
                  />
                ))}
              </div>
            )}
          </section>

          {matches.notes.length > 0 && (
            <section className="verified-section">
              <h3 className="verified-section-title">Notes</h3>
              <ul className="verified-notes">
                {matches.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </section>
          )}
        </div>

        {/*
        <details className="collapsible-section verified-raw-json">
          <summary>Raw JSON</summary>
          <pre className="aptitude-raw-pre">
            {JSON.stringify(matches, null, 2)}
          </pre>
        </details>
        */}
      </div>
    </details>
  );
}
