import { openDomPdf } from "./exportDomPdf";

function prepareInferenceConfidenceCloneForExport(
  _doc: Document,
  clone: HTMLElement
) {
  clone.classList.add(
    "aptitude-profile",
    "aptitude-inference-confidence",
    "aptitude-profile--pdf-export"
  );
}

export async function openInferenceConfidencePdf(
  element: HTMLElement
): Promise<void> {
  await openDomPdf(element, prepareInferenceConfidenceCloneForExport);
}
