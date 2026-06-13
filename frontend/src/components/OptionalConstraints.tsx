import { ClearInput, ClearSelect } from "./ClearField";
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
            <ClearSelect
              id="remote"
              value={constraints.remote_preference}
              defaultValue="any"
              clearLabel="Clear remote preference"
              onChange={(remote_preference) =>
                onChange({ ...constraints, remote_preference })
              }
            >
              <option value="any">any</option>
              <option value="remote">remote</option>
              <option value="hybrid">hybrid</option>
              <option value="onsite">onsite</option>
            </ClearSelect>
          </div>
          <div>
            <label htmlFor="salary">Salary min</label>
            <ClearInput
              id="salary"
              value={constraints.salary_min}
              clearLabel="Clear salary min"
              onChange={(salary_min) =>
                onChange({ ...constraints, salary_min })
              }
            />
          </div>
        </div>
        <div className="grid grid-2">
          <div>
            <label htmlFor="include">Industries include (comma-separated)</label>
            <ClearInput
              id="include"
              value={constraints.industries_include}
              clearLabel="Clear industries include"
              onChange={(industries_include) =>
                onChange({ ...constraints, industries_include })
              }
            />
          </div>
          <div>
            <label htmlFor="exclude">Industries exclude (comma-separated)</label>
            <ClearInput
              id="exclude"
              value={constraints.industries_exclude}
              clearLabel="Clear industries exclude"
              onChange={(industries_exclude) =>
                onChange({ ...constraints, industries_exclude })
              }
            />
          </div>
        </div>
      </div>
    </details>
  );
}
