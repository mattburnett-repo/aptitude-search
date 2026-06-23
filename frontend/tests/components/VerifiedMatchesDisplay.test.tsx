import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { VerifiedMatchesDisplay } from "../../src/components/VerifiedMatchesDisplay";
import verifiedMatches from "../fixtures/sample-verified-matches.json";

vi.mock("../../src/lib/exportVerifiedMatchesPdf", () => ({
  openVerifiedMatchesPdf: vi.fn(),
}));

import { openVerifiedMatchesPdf } from "../../src/lib/exportVerifiedMatchesPdf";

describe("VerifiedMatchesDisplay", () => {
  it("renders search plan, results, and notes", () => {
    render(<VerifiedMatchesDisplay matches={verifiedMatches} />);

    expect(screen.getByText("Search plan")).toBeInTheDocument();
    expect(screen.getByText("Django modernization roles")).toBeInTheDocument();
    expect(screen.getByText("Senior Software Engineer")).toBeInTheDocument();
    expect(screen.getByText("Riverbend Logistics")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "View posting" })
    ).toHaveAttribute("href", "https://example.com/jobs/senior-software-engineer");
    expect(screen.getByRole("heading", { name: "Notes" })).toBeInTheDocument();
    expect(
      screen.getAllByText(/Sample fixture for frontend display tests/).length
    ).toBeGreaterThan(0);
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
});
