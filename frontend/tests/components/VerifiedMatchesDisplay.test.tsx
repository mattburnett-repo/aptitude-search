import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VerifiedMatchesDisplay } from "../../src/components/VerifiedMatchesDisplay";
import verifiedMatches from "../fixtures/sample-verified-matches.json";

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
});
