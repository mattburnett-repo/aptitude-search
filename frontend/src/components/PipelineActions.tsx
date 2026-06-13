import { useEffect, useRef, useState } from "react";
import type { PipelineResult } from "../api/pipeline";
import {
  copyVerifiedMatches,
  exportPipelineResult,
} from "../lib/pipelineResults";

type PipelineActionsProps = {
  loading: boolean;
  canRun: boolean;
  result: PipelineResult | null;
  onRun: () => void;
};

const FEEDBACK_MS = 2000;

export function PipelineActions({
  loading,
  canRun,
  result,
  onRun,
}: PipelineActionsProps) {
  const [exportAck, setExportAck] = useState(false);
  const [copyAck, setCopyAck] = useState(false);
  const exportTimerRef = useRef<number | null>(null);
  const copyTimerRef = useRef<number | null>(null);

  useEffect(() => {
    setExportAck(false);
    setCopyAck(false);
  }, [result]);

  useEffect(() => {
    return () => {
      if (exportTimerRef.current !== null) {
        window.clearTimeout(exportTimerRef.current);
      }
      if (copyTimerRef.current !== null) {
        window.clearTimeout(copyTimerRef.current);
      }
    };
  }, []);

  function acknowledge(
    setter: (value: boolean) => void,
    timerRef: React.MutableRefObject<number | null>
  ) {
    setter(true);
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
    }
    timerRef.current = window.setTimeout(() => {
      setter(false);
      timerRef.current = null;
    }, FEEDBACK_MS);
  }

  function handleExport() {
    if (!result) return;
    exportPipelineResult(result);
    acknowledge(setExportAck, exportTimerRef);
  }

  async function handleCopy() {
    if (!result) return;
    await copyVerifiedMatches(result);
    acknowledge(setCopyAck, copyTimerRef);
  }

  const canExport =
    !loading && result != null && result.aptitude_profile != null;
  const canCopy =
    !loading && result != null && result.verified_matches != null;

  return (
    <div className="actions">
      <button type="button" disabled={loading || !canRun} onClick={onRun}>
        {loading ? "Running…" : "Go"}
      </button>
      {canExport && (
        <button
          type="button"
          className={`secondary${exportAck ? " success" : ""}`}
          onClick={handleExport}
        >
          {exportAck ? "Exported!" : "Export JSON"}
        </button>
      )}
      {canCopy && (
        <button
          type="button"
          className={`secondary${copyAck ? " success" : ""}`}
          onClick={() => void handleCopy()}
        >
          {copyAck ? "Copied!" : "Copy verified matches"}
        </button>
      )}
    </div>
  );
}
