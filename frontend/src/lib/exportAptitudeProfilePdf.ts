import { openDomPdf } from "./exportDomPdf";

function flattenInferenceConfidenceForExport(doc: Document, root: HTMLElement) {
  for (const details of root.querySelectorAll(".aptitude-meta")) {
    if (!(details instanceof HTMLDetailsElement)) continue;

    const summary = details.querySelector("summary");
    const body = details.querySelector(".collapsible-section-body");
    if (!summary || !body) continue;

    const section = doc.createElement("section");
    section.className = "aptitude-section aptitude-inference-confidence-pdf";

    const heading = doc.createElement("h3");
    heading.className = "aptitude-section-title";
    heading.textContent = summary.textContent?.trim() ?? "Inference confidence";
    section.appendChild(heading);

    while (body.firstChild) {
      section.appendChild(body.firstChild);
    }

    details.replaceWith(section);
  }
}

function prepareAptitudeProfileCloneForExport(doc: Document, clone: HTMLElement) {
  clone.classList.add("aptitude-profile", "aptitude-profile--pdf-export");
  flattenInferenceConfidenceForExport(doc, clone);
  for (const node of clone.querySelectorAll("details")) {
    if (node instanceof HTMLDetailsElement) {
      node.open = true;
    }
  }
}

export async function openAptitudeProfilePdf(element: HTMLElement): Promise<void> {
  await openDomPdf(element, prepareAptitudeProfileCloneForExport);
}
