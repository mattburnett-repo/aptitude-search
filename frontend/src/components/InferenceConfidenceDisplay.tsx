import { useRef } from "react";
import { SaveAsPdfToolbar, type StageNavProps } from "./SaveAsPdfToolbar";
import type { AptitudeProfile } from "./AptitudeProfileDisplay";

type Confidence = "high" | "medium" | "low";

type ConfidenceMapEntry = {
  confidence: Confidence;
  reason: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isConfidence(value: unknown): value is Confidence {
  return value === "high" || value === "medium" || value === "low";
}

function isAptitudeProfile(value: unknown): value is AptitudeProfile {
  if (!isRecord(value)) return false;
  return (
    typeof value.aptitude_summary === "string" &&
    Array.isArray(value.core_skills) &&
    Array.isArray(value.rationale)
  );
}

function ConfidenceBadge({ level }: { level: Confidence }) {
  return (
    <span className={`confidence-badge confidence-${level}`}>{level}</span>
  );
}

function InferenceSaveAsPdfToolbar({
  contentRef,
  stageNav,
  onPdfBusyChange,
}: {
  contentRef: React.RefObject<HTMLDivElement | null>;
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
}) {
  return (
    <SaveAsPdfToolbar
      contentRef={contentRef}
      stageNav={stageNav}
      onPdfBusyChange={onPdfBusyChange}
      loadExporter={async () => {
        const { openInferenceConfidencePdf } = await import(
          "../lib/exportInferenceConfidencePdf"
        );
        return openInferenceConfidencePdf;
      }}
    />
  );
}

type InferenceConfidenceDisplayProps = {
  profile: unknown;
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
};

export function InferenceConfidenceDisplay({
  profile,
  stageNav,
  onPdfBusyChange,
}: InferenceConfidenceDisplayProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  if (!profile) return null;

  if (!isAptitudeProfile(profile)) {
    return (
      <details className="collapsible-section" open>
        <summary>Step 2 — How sure we are</summary>
        {stageNav && (
          <InferenceSaveAsPdfToolbar
            contentRef={contentRef}
            stageNav={stageNav}
            onPdfBusyChange={onPdfBusyChange}
          />
        )}
        <div ref={contentRef} className="collapsible-section-body aptitude-profile">
          <pre className="aptitude-raw-pre">{JSON.stringify(profile, null, 2)}</pre>
        </div>
      </details>
    );
  }

  const confidenceEntries = Object.entries(profile.confidence_map ?? {}).filter(
    ([, entry]) =>
      isRecord(entry) &&
      isConfidence(entry.confidence) &&
      typeof entry.reason === "string"
  ) as [string, ConfidenceMapEntry][];

  return (
    <details className="collapsible-section" open>
      <summary>Step 2 — How sure we are</summary>
      {(confidenceEntries.length > 0 || stageNav) && (
        <InferenceSaveAsPdfToolbar
          contentRef={contentRef}
          stageNav={stageNav}
          onPdfBusyChange={onPdfBusyChange}
        />
      )}
      <div className="collapsible-section-body">
        {confidenceEntries.length === 0 ? (
          <div ref={contentRef}>
            <p className="stage2-empty">No confidence details available.</p>
          </div>
        ) : (
          <div ref={contentRef} className="aptitude-profile aptitude-inference-confidence">
            <div className="aptitude-pdf-page" data-pdf-page>
              <section className="aptitude-section aptitude-inference-confidence-section">
                <ul className="aptitude-confidence-map">
                  {confidenceEntries.map(([key, entry]) => (
                    <li key={key}>
                      <span className="aptitude-confidence-key">
                        {key.replace(/_/g, " ")}
                      </span>
                      <ConfidenceBadge level={entry.confidence} />
                      <p className="aptitude-evidence">{entry.reason}</p>
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          </div>
        )}

        {/*
        <details className="collapsible-section aptitude-raw-json">
          <summary>Raw JSON</summary>
          <pre className="aptitude-raw-pre">
            {JSON.stringify(profile.confidence_map ?? {}, null, 2)}
          </pre>
        </details>
        */}
      </div>
    </details>
  );
}
