import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { OccupationMatchesDisplay } from "../../src/components/OccupationMatchesDisplay";
import occupationMatches from "../fixtures/sample-occupation-matches.json";

vi.mock("../../src/lib/exportOccupationMatchesPdf", () => ({
  openOccupationMatchesPdf: vi.fn(),
}));

import { openOccupationMatchesPdf } from "../../src/lib/exportOccupationMatchesPdf";

describe("OccupationMatchesDisplay", () => {
  it("renders O*NET occupation matches from fixture", () => {
    render(<OccupationMatchesDisplay matches={occupationMatches} />);

    expect(screen.getByText("Web Developers")).toBeInTheDocument();
    expect(screen.getAllByText("medium")).toHaveLength(2);
    expect(screen.queryByText("0.6803")).not.toBeInTheDocument();
    expect(screen.queryByText("15-1254.00")).not.toBeInTheDocument();
    expect(screen.getByText("Software Developers")).toBeInTheDocument();
  });

  it("shows empty state for an empty array", () => {
    render(<OccupationMatchesDisplay matches={[]} />);

    expect(screen.getByText(/No matching careers/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save as PDF" })).not.toBeInTheDocument();
  });

  it("falls back to raw JSON for unknown shapes", () => {
    render(<OccupationMatchesDisplay matches={{ bad: true }} />);

    expect(screen.getByText(/"bad": true/)).toBeInTheDocument();
  });

  it("opens a PDF in a new tab when Save as PDF is clicked", async () => {
    const user = userEvent.setup();
    render(<OccupationMatchesDisplay matches={occupationMatches} />);

    await user.click(screen.getByRole("button", { name: "Save as PDF" }));

    expect(openOccupationMatchesPdf).toHaveBeenCalledTimes(1);
    expect(openOccupationMatchesPdf).toHaveBeenCalledWith(
      document.querySelector(".occupation-matches")
    );
  });
});
