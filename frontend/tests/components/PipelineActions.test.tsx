import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PipelineActions } from "../../src/components/PipelineActions";

describe("PipelineActions", () => {
  it("matches markup snapshot", () => {
    const { container } = render(
      <PipelineActions loading={false} canRun={true} onRun={() => {}} />
    );
    expect(container.querySelector(".actions")).toMatchSnapshot();
  });

  it("disables Go while loading or when resume input is missing", () => {
    const { rerender } = render(
      <PipelineActions loading={false} canRun={false} onRun={() => {}} />
    );

    expect(screen.getByRole("button", { name: "Go →" })).toBeDisabled();

    rerender(<PipelineActions loading={true} canRun={true} onRun={() => {}} />);

    expect(screen.getByRole("button", { name: "Running…" })).toBeDisabled();
  });

  it("enables Go when input is present and not loading", () => {
    render(<PipelineActions loading={false} canRun={true} onRun={() => {}} />);

    expect(screen.getByRole("button", { name: "Go →" })).toBeEnabled();
  });
});
