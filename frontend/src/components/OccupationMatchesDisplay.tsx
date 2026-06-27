import { useRef } from "react";
import { SaveAsPdfToolbar } from "./SaveAsPdfToolbar";

export type OccupationMatch = {
  onetsoc_code: string;
  title: string;
  score: number;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isOccupationMatch(value: unknown): value is OccupationMatch {
  if (!isRecord(value)) return false;
  return (
    typeof value.onetsoc_code === "string" &&
    typeof value.title === "string" &&
    typeof value.score === "number"
  );
}

function isOccupationMatches(value: unknown): value is OccupationMatch[] {
  return Array.isArray(value) && value.every(isOccupationMatch);
}

function formatScore(score: number): string {
  return score.toFixed(4);
}

function OccupationSaveAsPdfToolbar({
  matchesRef,
}: {
  matchesRef: React.RefObject<HTMLDivElement | null>;
}) {
  return (
    <SaveAsPdfToolbar
      contentRef={matchesRef}
      loadExporter={async () => {
        const { openOccupationMatchesPdf } = await import(
          "../lib/exportOccupationMatchesPdf"
        );
        return openOccupationMatchesPdf;
      }}
    />
  );
}

type OccupationMatchesDisplayProps = {
  matches: unknown;
};

export function OccupationMatchesDisplay({ matches }: OccupationMatchesDisplayProps) {
  const matchesRef = useRef<HTMLDivElement>(null);

  if (matches == null) return null;

  if (!isOccupationMatches(matches)) {
    return (
      <details className="collapsible-section" open>
        <summary>Stage 2 — O*NET occupation matches</summary>
        <div className="collapsible-section-body">
          <pre className="aptitude-raw-pre">{JSON.stringify(matches, null, 2)}</pre>
        </div>
      </details>
    );
  }

  return (
    <details className="collapsible-section" open>
      <summary>Stage 2 — O*NET occupation matches</summary>
      {matches.length > 0 && <OccupationSaveAsPdfToolbar matchesRef={matchesRef} />}
      <div className="collapsible-section-body">
        {matches.length === 0 ? (
          <p className="stage2-empty">
            No O*NET occupation matches (matching disabled or unavailable).
          </p>
        ) : (
          <div ref={matchesRef} className="occupation-matches">
            <section className="aptitude-section">
              <p className="stage2-lead">
                Top occupations by embedding similarity to your aptitude profile.
              </p>
              <ol className="occupation-match-list">
                {matches.map((match) => (
                  <li key={match.onetsoc_code} className="occupation-match-item">
                    <div className="occupation-match-header">
                      <span className="occupation-match-title">{match.title}</span>
                      <span className="occupation-match-score">
                        {formatScore(match.score)}
                      </span>
                    </div>
                    <span className="occupation-match-code">{match.onetsoc_code}</span>
                  </li>
                ))}
              </ol>
            </section>
          </div>
        )}

        <details className="collapsible-section aptitude-raw-json">
          <summary>Raw JSON</summary>
          <pre className="aptitude-raw-pre">{JSON.stringify(matches, null, 2)}</pre>
        </details>
      </div>
    </details>
  );
}
