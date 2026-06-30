import { useEffect, useState } from "react";

export type StageNavProps = {
  onBack: () => void;
  onNext: () => void;
  onStartOver: () => void;
  hideBack?: boolean;
  isLastStage?: boolean;
  disabled?: boolean;
};

type SaveAsPdfToolbarProps = {
  contentRef: React.RefObject<HTMLDivElement | null>;
  loadExporter: () => Promise<(element: HTMLElement) => Promise<void>>;
  stageNav?: StageNavProps;
  onPdfBusyChange?: (busy: boolean) => void;
};

export function SaveAsPdfToolbar({
  contentRef,
  loadExporter,
  stageNav,
  onPdfBusyChange,
}: SaveAsPdfToolbarProps) {
  const [pdfBusy, setPdfBusy] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const navDisabled = pdfBusy || stageNav?.disabled;

  useEffect(() => {
    onPdfBusyChange?.(pdfBusy);
  }, [pdfBusy, onPdfBusyChange]);

  async function handleSaveAsPdf() {
    const element = contentRef.current;
    if (!element || pdfBusy) return;

    setPdfError(null);
    setPdfBusy(true);
    try {
      const openPdf = await loadExporter();
      await openPdf(element);
    } catch (err) {
      setPdfError(
        err instanceof Error ? err.message : "Could not create PDF. Try again."
      );
    } finally {
      setPdfBusy(false);
    }
  }

  return (
    <div className="pdf-export-actions">
      <button
        type="button"
        disabled={pdfBusy}
        onClick={() => void handleSaveAsPdf()}
      >
        {pdfBusy ? "Generating PDF…" : "Save as PDF"}
      </button>
      {stageNav && (
        <div className="stage-nav-actions">
          {!stageNav.hideBack && (
            <button
              type="button"
              className="back"
              disabled={navDisabled}
              onClick={stageNav.onBack}
            >
              Back
            </button>
          )}
          {stageNav.isLastStage ? (
            <button
              type="button"
              className="secondary success"
              disabled={navDisabled}
              onClick={stageNav.onStartOver}
            >
              Start over
            </button>
          ) : (
            <button type="button" disabled={navDisabled} onClick={stageNav.onNext}>
              Next
            </button>
          )}
        </div>
      )}
      {pdfError && <p className="error pdf-export-error">{pdfError}</p>}
    </div>
  );
}
