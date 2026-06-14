import { afterEach, describe, expect, it, vi } from "vitest";
import { runPipelineStream } from "../../src/api/pipeline";
import { mockNdjsonStreamResponse } from "../helpers/streamResponse";

describe("runPipelineStream", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("parses chunked NDJSON progress and result events", async () => {
    const progress: string[] = [];
    const resultPayload = {
      aptitude_profile: { aptitude_summary: "ok" },
      verified_matches: { search_plan: [], results: [], notes: ["n"] },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockNdjsonStreamResponse([
          JSON.stringify({ type: "progress", message: "Stage 1 starting" }),
          JSON.stringify({ type: "progress", message: "Stage 2 starting" }),
          JSON.stringify({ type: "result", data: resultPayload }),
        ])
      )
    );

    const result = await runPipelineStream({ resume: "text" }, (message) => {
      progress.push(message);
    });

    expect(fetch).toHaveBeenCalledWith("/api/v1/pipeline?stream=1", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume: "text" }),
    });
    expect(progress).toEqual(["Stage 1 starting", "Stage 2 starting"]);
    expect(result).toEqual(resultPayload);
  });

  it("throws formatted HTTP errors with request_id", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: "Invalid resume",
            request_id: "req-123",
          }),
          { status: 422, statusText: "Unprocessable Entity" }
        )
      )
    );

    await expect(
      runPipelineStream({ resume: "" }, () => {})
    ).rejects.toThrow("Invalid resume (ref: req-123)");
  });

  it("throws stream error events with request_id", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockNdjsonStreamResponse([
          JSON.stringify({
            type: "error",
            detail: "Pipeline failed",
            request_id: "req-456",
          }),
        ])
      )
    );

    await expect(
      runPipelineStream({ resume: "text" }, () => {})
    ).rejects.toThrow("Pipeline failed (ref: req-456)");
  });

  it("throws when the stream finishes without a result", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockNdjsonStreamResponse([
          JSON.stringify({ type: "progress", message: "Working" }),
        ])
      )
    );

    await expect(
      runPipelineStream({ resume: "text" }, () => {})
    ).rejects.toThrow("Pipeline finished without a result.");
  });

  it("throws when response body is missing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    );

    await expect(
      runPipelineStream({ resume: "text" }, () => {})
    ).rejects.toThrow("No response body from server.");
  });
});
