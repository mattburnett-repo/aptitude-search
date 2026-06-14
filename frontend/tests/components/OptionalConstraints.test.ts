import { describe, expect, it } from "vitest";
import {
  buildConstraintsBody,
  defaultConstraints,
} from "../../src/components/OptionalConstraints";
import pipelineRequest from "../../../fixtures/pipeline-request-example.json";

describe("buildConstraintsBody", () => {
  it("maps defaults to empty strings and null salary", () => {
    expect(buildConstraintsBody(defaultConstraints)).toEqual({
      location: "",
      remote_preference: "any",
      salary_min: null,
      industries_include: [],
      industries_exclude: [],
    });
  });

  it("parses salary and comma-separated industries", () => {
    const body = buildConstraintsBody({
      location: "Toronto, ON",
      remote_preference: "remote",
      salary_min: "120000",
      industries_include: " SaaS , FinTech ",
      industries_exclude: " Gambling , ",
    });

    expect(body).toEqual({
      location: "Toronto, ON",
      remote_preference: "remote",
      salary_min: 120000,
      industries_include: ["SaaS", "FinTech"],
      industries_exclude: ["Gambling"],
    });
  });

  it("matches the committed pipeline request fixture constraints", () => {
    const { constraints } = pipelineRequest;
    expect(buildConstraintsBody({
      location: constraints.location,
      remote_preference: constraints.remote_preference,
      salary_min: String(constraints.salary_min),
      industries_include: constraints.industries_include.join(", "),
      industries_exclude: constraints.industries_exclude.join(", "),
    })).toEqual(constraints);
  });
});
