import { useRef } from "react";
import { SaveAsPdfToolbar } from "./SaveAsPdfToolbar";

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
}: {
  planRef: React.RefObject<HTMLDivElement | null>;
}) {
  return (
    <SaveAsPdfToolbar
      contentRef={planRef}
      loadExporter={async () => {
        const { openRoleFamilyPlanPdf } = await import("../lib/exportRoleFamilyPlanPdf");
        return openRoleFamilyPlanPdf;
      }}
    />
  );
}

type RoleFamilyPlanDisplayProps = {
  plan: unknown;
};

export function RoleFamilyPlanDisplay({ plan }: RoleFamilyPlanDisplayProps) {
  const planRef = useRef<HTMLDivElement>(null);

  if (!plan) return null;

  if (!isRoleFamilyPlan(plan)) {
    return (
      <details className="collapsible-section" open>
        <summary>Stage 2 — Role family plan</summary>
        <div className="collapsible-section-body">
          <pre className="aptitude-raw-pre">{JSON.stringify(plan, null, 2)}</pre>
        </div>
      </details>
    );
  }

  return (
    <details className="collapsible-section" open>
      <summary>Stage 2 — Role family plan</summary>
      <RoleFamilySaveAsPdfToolbar planRef={planRef} />
      <div className="collapsible-section-body">
        <div ref={planRef} className="role-family-plan">
          {plan.recommended_role_families.map((family) => (
            <section key={family.role_family} className="aptitude-section role-family-card">
              <h3 className="aptitude-section-title">{family.role_family}</h3>
              <p className="role-family-fit-reason">{family.fit_reason}</p>
              <TagList label="Search terms" items={family.search_terms} />
              <TagList label="Work modes" items={family.work_modes} />
              <TagList label="Supporting signals" items={family.supporting_signals} />
              <TagList label="Avoid terms" items={family.avoid_terms} />
            </section>
          ))}

          {plan.rationale.length > 0 && (
            <section className="aptitude-section aptitude-rationale-section">
              <h3 className="aptitude-section-title">Rationale</h3>
              <ul className="aptitude-rationale">
                {plan.rationale.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <details className="collapsible-section aptitude-raw-json">
          <summary>Raw JSON</summary>
          <pre className="aptitude-raw-pre">{JSON.stringify(plan, null, 2)}</pre>
        </details>
      </div>
    </details>
  );
}
