import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultConstraints } from "../../src/components/OptionalConstraints";
import { defaultResumeInput } from "../../src/components/ResumeInput";
import { runPipelineStream } from "../../src/api/pipeline";
import { readFileAsBase64 } from "../../src/lib/readFileAsBase64";
import { usePipeline } from "../../src/hooks/usePipeline";
import stage1Profile from "../../../fixtures/example-outputs/career-changer-mixed-stack-stage1.json";
import verifiedMatches from "../fixtures/sample-verified-matches.json";

vi.mock("../../src/api/pipeline", () => ({
  runPipelineStream: vi.fn(),
}));

vi.mock("../../src/lib/readFileAsBase64", () => ({
  readFileAsBase64: vi.fn(),
}));

describe("usePipeline", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("posts text resume and constraints, then stores the result", async () => {
    const pipelineResult = {
      aptitude_profile: stage1Profile,
      verified_matches: verifiedMatches,
    };
    vi.mocked(runPipelineStream).mockImplementation(async (_body, onProgress) => {
      onProgress("Stage 1 complete");
      return pipelineResult;
    });

    const { result } = renderHook(() => usePipeline());

    await result.current.runPipeline(
      { ...defaultResumeInput, resume: "Alex Morgan" },
      defaultConstraints
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(runPipelineStream).toHaveBeenCalledWith(
      {
        resume: "Alex Morgan",
        constraints: {
          location: "",
          remote_preference: "any",
          salary_min: null,
          industries_include: [],
          industries_exclude: [],
        },
      },
      expect.any(Function)
    );
    await waitFor(() => {
      expect(result.current.progressMessages).toEqual(["Stage 1 complete"]);
    });
    expect(result.current.result).toEqual(pipelineResult);
    expect(result.current.error).toBeNull();
  });

  it("sends PDF resumes as base64", async () => {
    const pdfFile = new File(["pdf"], "resume.pdf", { type: "application/pdf" });
    vi.mocked(readFileAsBase64).mockResolvedValue("encoded-pdf");
    vi.mocked(runPipelineStream).mockResolvedValue({
      aptitude_profile: stage1Profile,
      verified_matches: verifiedMatches,
    });

    const { result } = renderHook(() => usePipeline());

    await result.current.runPipeline(
      { resume: "", pdfFile, fileName: "resume.pdf" },
      defaultConstraints
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(readFileAsBase64).toHaveBeenCalledWith(pdfFile);
    expect(runPipelineStream).toHaveBeenCalledWith(
      expect.objectContaining({
        resume: "",
        resume_pdf_base64: "encoded-pdf",
      }),
      expect.any(Function)
    );
  });

  it("surfaces API errors", async () => {
    vi.mocked(runPipelineStream).mockRejectedValue(new Error("Invalid resume"));

    const { result } = renderHook(() => usePipeline());

    await result.current.runPipeline(
      { ...defaultResumeInput, resume: "text" },
      defaultConstraints
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    await waitFor(() => expect(result.current.error).toBe("Invalid resume"));
    expect(result.current.result).toBeNull();
  });
});
