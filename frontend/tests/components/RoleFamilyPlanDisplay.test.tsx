import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RoleFamilyPlanDisplay } from "../../src/components/RoleFamilyPlanDisplay";
import roleFamilyPlan from "../../../fixtures/example-outputs/career-changer-role-family-plan.json";

vi.mock("../../src/lib/exportRoleFamilyPlanPdf", () => ({
  openRoleFamilyPlanPdf: vi.fn(),
}));

import { openRoleFamilyPlanPdf } from "../../src/lib/exportRoleFamilyPlanPdf";

describe("RoleFamilyPlanDisplay", () => {
  it("renders collapsed role families from the stage 2 fixture", () => {
    render(<RoleFamilyPlanDisplay plan={roleFamilyPlan} />);

    const summary = screen.getByText("Role: Solutions / Integration Engineering");
    const details = summary.closest("details");
    expect(details).toBeInstanceOf(HTMLDetailsElement);
    expect(details).not.toHaveAttribute("open");
    expect(document.querySelector(".aptitude-rationale")).toHaveTextContent(
      /Profile emphasizes integration/
    );
  });

  it("expands a role to show its details", async () => {
    const user = userEvent.setup();
    render(<RoleFamilyPlanDisplay plan={roleFamilyPlan} />);

    await user.click(
      screen.getByText("Role: Solutions / Integration Engineering")
    );

    const details = screen
      .getByText("Role: Solutions / Integration Engineering")
      .closest("details");
    expect(details).toHaveAttribute("open");
    expect(document.querySelector(".role-family-fit-reason")).toHaveTextContent(
      /Repeated API integrations/
    );
    expect(screen.getByText("solutions engineer")).toBeInTheDocument();
  });

  it("falls back to raw JSON for unknown shapes", () => {
    render(<RoleFamilyPlanDisplay plan={{ unexpected: true }} />);

    expect(screen.getByText(/"unexpected": true/)).toBeInTheDocument();
  });

  it("opens a PDF in a new tab when Save as PDF is clicked", async () => {
    const user = userEvent.setup();
    render(<RoleFamilyPlanDisplay plan={roleFamilyPlan} />);

    await user.click(screen.getByRole("button", { name: "Save as PDF" }));

    expect(openRoleFamilyPlanPdf).toHaveBeenCalledTimes(1);
    expect(openRoleFamilyPlanPdf).toHaveBeenCalledWith(
      document.querySelector(".role-family-plan")
    );
  });
});
