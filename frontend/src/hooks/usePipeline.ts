import { useState } from "react";
import {
  buildConstraintsBody,
  type Constraints,
} from "../components/OptionalConstraints";
import type { ResumeInputValue } from "../components/ResumeInput";
import { runPipelineStream, type PipelineResult } from "../api/pipeline";
import { readFileAsBase64 } from "../lib/readFileAsBase64";

export function usePipeline() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const [result, setResult] = useState<PipelineResult | null>(null);

  async function runPipeline(
    resumeInput: ResumeInputValue,
    constraints: Constraints
  ) {
    setError(null);
    setResult(null);
    setProgressMessages([]);
    setLoading(true);
    try {
      const body = resumeInput.pdfFile
        ? {
            resume: "",
            resume_pdf_base64: await readFileAsBase64(resumeInput.pdfFile),
            constraints: buildConstraintsBody(constraints),
          }
        : {
            resume: resumeInput.resume,
            constraints: buildConstraintsBody(constraints),
          };
      const data = await runPipelineStream(body, (message) => {
        setProgressMessages((prev) => [...prev, message]);
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return {
    loading,
    error,
    setError,
    progressMessages,
    result,
    runPipeline,
  };
}
