import { useRef } from "react";
import { SaveAsPdfToolbar } from "./SaveAsPdfToolbar";

type Confidence = "high" | "medium" | "low";

type SkillItem = {
  name: string;
  confidence: Confidence;
  evidence_from_resume?: string;
};

type LabeledItem = {
  label: string;
  confidence: Confidence;
  evidence_from_resume?: string;
};

type ConfidenceMapEntry = {
  confidence: Confidence;
  reason: string;
};

export type AptitudeProfile = {
  core_skills: SkillItem[];
  secondary_skills: SkillItem[];
  domains: LabeledItem[];
  strengths: LabeledItem[];
  adjacent_roles: LabeledItem[];
  seniority_band: string;
  working_style_signals: LabeledItem[];
  aptitude_summary: string;
  confidence_map: Record<string, ConfidenceMapEntry>;
  rationale: string[];
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

function SkillList({ title, items }: { title: string; items: SkillItem[] }) {
  if (items.length === 0) return null;
  return (
    <section className="aptitude-section">
      <h3 className="aptitude-section-title">{title}</h3>
      <ul className="aptitude-item-list">
        {items.map((item) => (
          <li key={item.name} className="aptitude-item">
            <div className="aptitude-item-header">
              <span className="aptitude-item-label">{item.name}</span>
              <ConfidenceBadge level={item.confidence} />
            </div>
            {item.evidence_from_resume && (
              <p className="aptitude-evidence">{item.evidence_from_resume}</p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function LabeledList({ title, items }: { title: string; items: LabeledItem[] }) {
  if (items.length === 0) return null;
  return (
    <section className="aptitude-section">
      <h3 className="aptitude-section-title">{title}</h3>
      <ul className="aptitude-item-list">
        {items.map((item) => (
          <li key={item.label} className="aptitude-item">
            <div className="aptitude-item-header">
              <span className="aptitude-item-label">{item.label}</span>
              <ConfidenceBadge level={item.confidence} />
            </div>
            {item.evidence_from_resume && (
              <p className="aptitude-evidence">{item.evidence_from_resume}</p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

type SaveAsPdfToolbarProps = {
  profileRef: React.RefObject<HTMLDivElement | null>;
};

function AptitudeSaveAsPdfToolbar({
  profileRef,
}: SaveAsPdfToolbarProps) {
  return (
    <SaveAsPdfToolbar
      contentRef={profileRef}
      loadExporter={async () => {
        const { openAptitudeProfilePdf } = await import(
          "../lib/exportAptitudeProfilePdf"
        );
        return openAptitudeProfilePdf;
      }}
    />
  );
}

type AptitudeProfileDisplayProps = {
  profile: unknown;
};

export function AptitudeProfileDisplay({ profile }: AptitudeProfileDisplayProps) {
  const profileRef = useRef<HTMLDivElement>(null);

  if (!profile) return null;

  if (!isAptitudeProfile(profile)) {
    return (
      <details className="collapsible-section" open>
        <summary>Stage 1 — Aptitude profile</summary>
        <AptitudeSaveAsPdfToolbar profileRef={profileRef} />
        <div ref={profileRef} className="collapsible-section-body aptitude-profile">
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
      <summary>Stage 1 — Aptitude profile</summary>
      <AptitudeSaveAsPdfToolbar profileRef={profileRef} />
      <div className="collapsible-section-body">
        <div ref={profileRef} className="aptitude-profile">
          <div className="aptitude-pdf-page" data-pdf-page>
            <p className="aptitude-summary">{profile.aptitude_summary}</p>

            <p className="aptitude-seniority">
              Seniority band:{" "}
              <span className="seniority-badge">{profile.seniority_band}</span>
            </p>

            <div className="aptitude-grid">
              <SkillList title="Core skills" items={profile.core_skills} />
              <SkillList title="Secondary skills" items={profile.secondary_skills} />
            </div>
          </div>

          <div className="aptitude-pdf-page" data-pdf-page>
            <div className="aptitude-grid">
              <LabeledList title="Domains" items={profile.domains} />
              <LabeledList title="Strengths" items={profile.strengths} />
            </div>
          </div>

          <div className="aptitude-pdf-page" data-pdf-page>
            <div className="aptitude-grid">
              <LabeledList title="Adjacent roles" items={profile.adjacent_roles} />
              <LabeledList
                title="Working style signals"
                items={profile.working_style_signals}
              />
            </div>

            {profile.rationale.length > 0 && (
              <section className="aptitude-section aptitude-rationale-section">
                <h3 className="aptitude-section-title">Rationale</h3>
                <ul className="aptitude-rationale">
                  {profile.rationale.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            )}
          </div>

          {confidenceEntries.length > 0 && (
            <div className="aptitude-pdf-page" data-pdf-page>
              <details className="collapsible-section aptitude-meta">
                <summary>Inference confidence</summary>
                <div className="collapsible-section-body">
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
                </div>
              </details>
            </div>
          )}
        </div>

        <details className="collapsible-section aptitude-raw-json">
          <summary>Raw JSON</summary>
          <pre className="aptitude-raw-pre">
            {JSON.stringify(profile, null, 2)}
          </pre>
        </details>
      </div>
    </details>
  );
}
