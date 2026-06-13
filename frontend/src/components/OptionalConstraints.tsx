import { LocationInput } from "./LocationInput";

export type Constraints = {
  location: string;
  remote_preference: string;
  salary_min: string;
  industries_include: string;
  industries_exclude: string;
};

export const defaultConstraints: Constraints = {
  location: "",
  remote_preference: "any",
  salary_min: "",
  industries_include: "",
  industries_exclude: "",
};

export function buildConstraintsBody(constraints: Constraints) {
  return {
    location: constraints.location,
    remote_preference: constraints.remote_preference,
    salary_min: constraints.salary_min ? Number(constraints.salary_min) : null,
    industries_include: constraints.industries_include
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
    industries_exclude: constraints.industries_exclude
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
  };
}

type OptionalConstraintsProps = {
  constraints: Constraints;
  onChange: (constraints: Constraints) => void;
};

export function OptionalConstraints({
  constraints,
  onChange,
}: OptionalConstraintsProps) {
  return (
    <details className="collapsible-section">
      <summary>Optional constraints</summary>
      <div className="collapsible-section-body">
        <div className="grid grid-3">
          <div>
            <label htmlFor="location">Location</label>
            <LocationInput
              id="location"
              value={constraints.location}
              onChange={(location) =>
                onChange({ ...constraints, location })
              }
            />
          </div>
          <div>
            <label htmlFor="remote">Remote preference</label>
            <select
              id="remote"
              value={constraints.remote_preference}
              onChange={(e) =>
                onChange({
                  ...constraints,
                  remote_preference: e.target.value,
                })
              }
            >
              <option value="any">any</option>
              <option value="remote">remote</option>
              <option value="hybrid">hybrid</option>
              <option value="onsite">onsite</option>
            </select>
          </div>
          <div>
            <label htmlFor="salary">Salary min</label>
            <input
              id="salary"
              value={constraints.salary_min}
              onChange={(e) =>
                onChange({ ...constraints, salary_min: e.target.value })
              }
            />
          </div>
        </div>
        <div className="grid grid-2">
          <div>
            <label htmlFor="include">Industries include (comma-separated)</label>
            <input
              id="include"
              value={constraints.industries_include}
              onChange={(e) =>
                onChange({
                  ...constraints,
                  industries_include: e.target.value,
                })
              }
            />
          </div>
          <div>
            <label htmlFor="exclude">Industries exclude (comma-separated)</label>
            <input
              id="exclude"
              value={constraints.industries_exclude}
              onChange={(e) =>
                onChange({
                  ...constraints,
                  industries_exclude: e.target.value,
                })
              }
            />
          </div>
        </div>
      </div>
    </details>
  );
}
