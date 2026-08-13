import { useRef } from "react";
import { SaveAsPdfToolbar, type StageNavProps } from "./SaveAsPdfToolbar";

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
  culture_preferences: LabeledItem[];
  interests: LabeledItem[];
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

function AptitudeSaveAsPdfToolbar({
  profileRef,
  stageNav,
  onPdfBusyChange,
}: {
  profileRef: React.RefObject<HTMLDivElement | null>;
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
}) {
  return (
    <SaveAsPdfToolbar
      contentRef={profileRef}
      stageNav={stageNav}
      onPdfBusyChange={onPdfBusyChange}
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
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
};

export function AptitudeProfileDisplay({
  profile,
  stageNav,
  onPdfBusyChange,
}: AptitudeProfileDisplayProps) {
  const profileRef = useRef<HTMLDivElement>(null);

  if (!profile) return null;

  if (!isAptitudeProfile(profile)) {
    return (
      <details className="collapsible-section" open>
        <summary>Step 1 — From your resume</summary>
        <AptitudeSaveAsPdfToolbar
          profileRef={profileRef}
          stageNav={stageNav}
          onPdfBusyChange={onPdfBusyChange}
        />
        <div ref={profileRef} className="collapsible-section-body aptitude-profile">
          <pre className="aptitude-raw-pre">{JSON.stringify(profile, null, 2)}</pre>
        </div>
      </details>
    );
  }

  return (
    <details className="collapsible-section" open>
      <summary>Step 1 — From your resume</summary>
      <AptitudeSaveAsPdfToolbar
        profileRef={profileRef}
        stageNav={stageNav}
        onPdfBusyChange={onPdfBusyChange}
      />
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

          <div
            className="aptitude-pdf-page aptitude-profile-section-divider"
            data-pdf-page
          >
            <div className="aptitude-grid">
              <LabeledList title="Industry experience" items={profile.domains} />
              <LabeledList title="Strengths" items={profile.strengths} />
            </div>
          </div>

          <div
            className="aptitude-pdf-page aptitude-profile-section-divider"
            data-pdf-page
          >
            <div className="aptitude-grid">
              <LabeledList title="Adjacent roles" items={profile.adjacent_roles} />
              <LabeledList
                title="Working style signals"
                items={profile.working_style_signals}
              />
              <LabeledList
                title="Culture preferences"
                items={profile.culture_preferences ?? []}
              />
              <LabeledList title="Interests" items={profile.interests ?? []} />
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

        </div>
      </div>
    </details>
  );
}
