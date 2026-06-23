import { openDomPdf } from "./exportDomPdf";

function prepareVerifiedMatchesCloneForExport(_doc: Document, clone: HTMLElement) {
  clone.classList.add("verified-matches", "verified-matches--pdf-export");
}

export async function openVerifiedMatchesPdf(element: HTMLElement): Promise<void> {
  await openDomPdf(element, prepareVerifiedMatchesCloneForExport);
}
