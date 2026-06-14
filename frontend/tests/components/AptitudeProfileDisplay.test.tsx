import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AptitudeProfileDisplay } from "../../src/components/AptitudeProfileDisplay";
import stage1Profile from "../../../fixtures/example-outputs/career-changer-mixed-stack-stage1.json";

describe("AptitudeProfileDisplay", () => {
  it("renders structured profile content from the stage 1 fixture", () => {
    render(<AptitudeProfileDisplay profile={stage1Profile} />);

    expect(document.querySelector(".aptitude-summary")).toHaveTextContent(
      /Adaptable full-stack engineer who repeatedly succeeds/
    );
    expect(screen.getByRole("heading", { name: "Core skills" })).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(document.querySelector(".seniority-badge")).toHaveTextContent("senior");
  });

  it("falls back to raw JSON for unknown profile shapes", () => {
    render(<AptitudeProfileDisplay profile={{ unexpected: true }} />);

    expect(screen.getByText(/"unexpected": true/)).toBeInTheDocument();
  });
});
