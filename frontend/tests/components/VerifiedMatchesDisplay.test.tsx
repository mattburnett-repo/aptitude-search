import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { VerifiedMatchesDisplay } from "../../src/components/VerifiedMatchesDisplay";
import verifiedMatches from "../fixtures/sample-verified-matches.json";

vi.mock("../../src/lib/exportVerifiedMatchesPdf", () => ({
  openVerifiedMatchesPdf: vi.fn(),
}));

import { openVerifiedMatchesPdf } from "../../src/lib/exportVerifiedMatchesPdf";

describe("VerifiedMatchesDisplay", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("renders search plan, collapsed results, and notes", () => {
    render(<VerifiedMatchesDisplay matches={verifiedMatches} />);

    expect(screen.getByText("What we looked for")).toBeInTheDocument();
    expect(screen.getByText("Django modernization roles")).toBeInTheDocument();

    const role = screen.getByText("Senior Software Engineer");
    const details = role.closest("details");
    expect(details).toBeInstanceOf(HTMLDetailsElement);
    expect(details).not.toHaveAttribute("open");
    expect(screen.getByText("Riverbend Logistics")).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Notes" })).toBeInTheDocument();
    expect(
      screen.getAllByText(/Sample fixture for frontend display tests/).length
    ).toBeGreaterThan(0);
  });

  it("expands a job posting to show its details", async () => {
    const user = userEvent.setup();
    render(<VerifiedMatchesDisplay matches={verifiedMatches} />);

    await user.click(screen.getByText("Senior Software Engineer"));

    const details = screen
      .getByText("Senior Software Engineer")
      .closest("details");
    expect(details).toHaveAttribute("open");
    expect(
      screen.getByRole("link", { name: "View posting" })
    ).toHaveAttribute("href", "https://example.com/jobs/senior-software-engineer");
    expect(
      screen.getByText(/Matches Python, Django, and legacy modernization/)
    ).toBeInTheDocument();
  });

  it("falls back to raw JSON for unknown match shapes", () => {
    render(<VerifiedMatchesDisplay matches={{ partial: true }} />);

    expect(screen.getByText(/"partial": true/)).toBeInTheDocument();
  });

  it("opens a PDF in a new tab when Save as PDF is clicked", async () => {
    const user = userEvent.setup();
    render(<VerifiedMatchesDisplay matches={verifiedMatches} />);

    await user.click(screen.getByRole("button", { name: "Save as PDF" }));

    expect(openVerifiedMatchesPdf).toHaveBeenCalledTimes(1);
    expect(openVerifiedMatchesPdf).toHaveBeenCalledWith(
      document.querySelector(".verified-matches")
    );
  });

  it("shows a support footnote when results exist and support URL is set", async () => {
    vi.stubEnv("VITE_SUPPORT_URL", "https://buymeacoffee.com/aptitude.search");
    const { VerifiedMatchesDisplay: Display } = await import(
      "../../src/components/VerifiedMatchesDisplay"
    );

    render(<Display matches={verifiedMatches} />);

    const donations = screen.getByRole("link", { name: "Donations" });
    expect(donations).toHaveAttribute(
      "href",
      "https://buymeacoffee.com/aptitude.search",
    );
    expect(document.querySelector(".verified-results-support")).toHaveTextContent(
      "Helpful? Donations are always appreciated.",
    );
  });

  it("hides the support footnote when there are zero results", async () => {
    vi.stubEnv("VITE_SUPPORT_URL", "https://buymeacoffee.com/aptitude.search");
    const { VerifiedMatchesDisplay: Display } = await import(
      "../../src/components/VerifiedMatchesDisplay"
    );

    render(
      <Display
        matches={{
          search_plan: ["Example query"],
          results: [],
          notes: ["No matches in this test run."],
        }}
      />,
    );

    expect(screen.queryByText(/Helpful\?/)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Donations" })).not.toBeInTheDocument();
  });
});
