import { useRef } from "react";
import { SaveAsPdfToolbar, type StageNavProps } from "./SaveAsPdfToolbar";

type RoleFamily = {
  role_family: string;
  fit_reason: string;
  supporting_signals: string[];
  work_modes: string[];
  search_terms: string[];
  avoid_terms: string[];
};

export type RoleFamilyPlan = {
  recommended_role_families: RoleFamily[];
  rationale: string[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isRoleFamily(value: unknown): value is RoleFamily {
  if (!isRecord(value)) return false;
  return (
    typeof value.role_family === "string" &&
    typeof value.fit_reason === "string" &&
    isStringArray(value.supporting_signals) &&
    isStringArray(value.work_modes) &&
    isStringArray(value.search_terms) &&
    isStringArray(value.avoid_terms)
  );
}

function isRoleFamilyPlan(value: unknown): value is RoleFamilyPlan {
  if (!isRecord(value)) return false;
  return (
    Array.isArray(value.recommended_role_families) &&
    value.recommended_role_families.every(isRoleFamily) &&
    isStringArray(value.rationale)
  );
}

function TagList({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="role-family-tags">
      <span className="role-family-tags-label">{label}</span>
      <ul className="role-family-tag-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function RoleFamilySaveAsPdfToolbar({
  planRef,
  stageNav,
  onPdfBusyChange,
}: {
  planRef: React.RefObject<HTMLDivElement | null>;
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
}) {
  return (
    <SaveAsPdfToolbar
      contentRef={planRef}
      stageNav={stageNav}
      onPdfBusyChange={onPdfBusyChange}
      loadExporter={async () => {
        const { openRoleFamilyPlanPdf } = await import("../lib/exportRoleFamilyPlanPdf");
        return openRoleFamilyPlanPdf;
      }}
    />
  );
}

type RoleFamilyPlanDisplayProps = {
  plan: unknown;
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
};

export function RoleFamilyPlanDisplay({
  plan,
  stageNav,
  onPdfBusyChange,
}: RoleFamilyPlanDisplayProps) {
  const planRef = useRef<HTMLDivElement>(null);

  if (!plan) return null;

  if (!isRoleFamilyPlan(plan)) {
    return (
      <details className="collapsible-section" open>
        <summary>Step 4 — Recommended roles</summary>
        <div className="collapsible-section-body">
          <pre className="aptitude-raw-pre">{JSON.stringify(plan, null, 2)}</pre>
        </div>
      </details>
    );
  }

  return (
    <details className="collapsible-section" open>
      <summary>Step 4 — Recommended roles</summary>
      <RoleFamilySaveAsPdfToolbar
        planRef={planRef}
        stageNav={stageNav}
        onPdfBusyChange={onPdfBusyChange}
      />
      <div className="collapsible-section-body">
        <div ref={planRef} className="role-family-plan">
          <p className="stage2-lead role-family-lead">
            Select a role to see why we recommend it, keywords to use when
            searching, preferred work setup, details from your resume that
            support the fit, and keywords to skip.
          </p>
          {plan.recommended_role_families.map((family) => (
            <details
              key={family.role_family}
              className="collapsible-section role-family-card"
            >
              <summary>Role: {family.role_family}</summary>
              <div className="collapsible-section-body">
                <p className="role-family-tags-label">Why it fits</p>
                <p className="role-family-fit-reason">{family.fit_reason}</p>
                <TagList label="Job search keywords" items={family.search_terms} />
                <TagList label="Work setup" items={family.work_modes} />
                <TagList
                  label="From your resume"
                  items={family.supporting_signals}
                />
                <TagList label="Skip these keywords" items={family.avoid_terms} />
              </div>
            </details>
          ))}

          {plan.rationale.length > 0 && (
            <section className="aptitude-section aptitude-rationale-section">
              <h3 className="aptitude-section-title">Why these roles</h3>
              <ul className="aptitude-rationale">
                {plan.rationale.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          )}
        </div>

      </div>
    </details>
  );
}
