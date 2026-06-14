import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { PipelineActions } from "../../src/components/PipelineActions";
import stage1Profile from "../../../fixtures/example-outputs/career-changer-mixed-stack-stage1.json";
import verifiedMatches from "../fixtures/sample-verified-matches.json";

vi.mock("../../src/lib/pipelineResults", () => ({
  exportPipelineResult: vi.fn(),
  copyVerifiedMatches: vi.fn().mockResolvedValue(undefined),
}));

import {
  copyVerifiedMatches,
  exportPipelineResult,
} from "../../src/lib/pipelineResults";

describe("PipelineActions", () => {
  it("disables Go while loading or when resume input is missing", () => {
    const { rerender } = render(
      <PipelineActions
        loading={false}
        canRun={false}
        result={null}
        onRun={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: "Go" })).toBeDisabled();

    rerender(
      <PipelineActions
        loading={true}
        canRun={true}
        result={null}
        onRun={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: "Running…" })).toBeDisabled();
  });

  it("shows export and copy actions when result sections are present", async () => {
    const user = userEvent.setup();
    const result = {
      aptitude_profile: stage1Profile,
      verified_matches: verifiedMatches,
    };

    render(
      <PipelineActions
        loading={false}
        canRun={true}
        result={result}
        onRun={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: "Export JSON" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Copy verified matches" })
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Export JSON" }));
    expect(exportPipelineResult).toHaveBeenCalledWith(result);

    await user.click(screen.getByRole("button", { name: "Copy verified matches" }));
    expect(copyVerifiedMatches).toHaveBeenCalledWith(result);
  });

  it("hides export and copy when result sections are missing", () => {
    render(
      <PipelineActions
        loading={false}
        canRun={true}
        result={{ aptitude_profile: null, verified_matches: null }}
        onRun={() => {}}
      />
    );

    expect(
      screen.queryByRole("button", { name: "Export JSON" })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Copy verified matches" })
    ).not.toBeInTheDocument();
  });
});
