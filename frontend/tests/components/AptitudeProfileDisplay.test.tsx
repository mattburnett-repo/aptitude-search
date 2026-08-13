import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AptitudeProfileDisplay } from "../../src/components/AptitudeProfileDisplay";
import stage1Profile from "../../../fixtures/example-outputs/career-changer-mixed-stack-stage1.json";

vi.mock("../../src/lib/exportAptitudeProfilePdf", () => ({
  openAptitudeProfilePdf: vi.fn(),
}));

import { openAptitudeProfilePdf } from "../../src/lib/exportAptitudeProfilePdf";

describe("AptitudeProfileDisplay", () => {
  it("matches markup snapshot", () => {
    const { container } = render(
      <AptitudeProfileDisplay profile={stage1Profile} />
    );
    expect(container.querySelector(".aptitude-profile")).toMatchSnapshot();
  });

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

  it("opens a PDF in a new tab when Save as PDF is clicked", async () => {
    const user = userEvent.setup();
    render(<AptitudeProfileDisplay profile={stage1Profile} />);

    await user.click(screen.getByRole("button", { name: "Save as PDF" }));

    expect(openAptitudeProfilePdf).toHaveBeenCalledTimes(1);
    expect(openAptitudeProfilePdf).toHaveBeenCalledWith(
      document.querySelector(".aptitude-profile")
    );
  });

  it("groups profile sections into PDF page breaks", () => {
    render(<AptitudeProfileDisplay profile={stage1Profile} />);

    const pages = document.querySelectorAll(".aptitude-profile [data-pdf-page]");
    expect(pages).toHaveLength(3);
    expect(pages[0]).toHaveTextContent(/Adaptable full-stack engineer/);
    expect(pages[0]).toHaveTextContent("Core skills");
    expect(pages[0]).not.toHaveTextContent("Industry experience");
    expect(pages[1]).toHaveTextContent("Industry experience");
    expect(pages[1]).toHaveTextContent("Strengths");
    expect(pages[2]).toHaveTextContent("Adjacent roles");
    expect(pages[2]).toHaveTextContent("Working style signals");
    expect(pages[2]).toHaveTextContent("Culture preferences");
    expect(pages[2]).not.toHaveTextContent("Inference confidence");
  });
});
