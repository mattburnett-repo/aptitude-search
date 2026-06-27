import {
  isPdfPageEmpty,
  maxSourceHeightPx,
  openPackedDomPdf,
} from "./exportDomPdf";

function prepareOccupationMatchesCloneForExport(_doc: Document, clone: HTMLElement) {
  clone.classList.add("occupation-matches", "occupation-matches--pdf-export");
}

type MeasuredItem = {
  element: HTMLElement;
  height: number;
};

type OccupationExportParts = {
  leading: HTMLElement[];
  items: MeasuredItem[];
  itemGap: number;
};

type PdfPagePlan = {
  leading: HTMLElement[];
  items: MeasuredItem[];
};

function createPageShell(width: number): HTMLElement {
  const page = document.createElement("div");
  page.className = "occupation-matches occupation-matches--pdf-export";
  page.style.width = `${width}px`;
  prepareOccupationMatchesCloneForExport(document, page);
  return page;
}

function measureBlocks(
  staging: HTMLElement,
  width: number,
  blocks: HTMLElement[]
): number {
  if (blocks.length === 0) return 0;

  const probe = createPageShell(width);
  for (const block of blocks) {
    probe.appendChild(block);
  }
  staging.appendChild(probe);
  void probe.offsetHeight;
  const height = probe.getBoundingClientRect().height;

  for (const block of blocks) {
    probe.removeChild(block);
  }
  staging.removeChild(probe);
  return height;
}

function listItemGapPx(list: HTMLElement): number {
  const items = list.querySelectorAll(".occupation-match-item");
  if (items.length < 2) return 0;
  const first = items[0].getBoundingClientRect();
  const second = items[1].getBoundingClientRect();
  return Math.max(0, second.top - first.bottom);
}

function parseOccupationExportParts(working: HTMLElement): OccupationExportParts {
  const leading: HTMLElement[] = [];
  const lead = working.querySelector<HTMLElement>(".stage2-lead");
  if (lead && !isPdfPageEmpty(lead)) {
    leading.push(lead);
  }

  const list = working.querySelector<HTMLElement>(".occupation-match-list");
  const items = list
    ? Array.from(list.querySelectorAll<HTMLElement>(".occupation-match-item")).map(
        (element) => ({
          element,
          height: element.getBoundingClientRect().height,
        })
      )
    : [];

  const itemGap = list ? listItemGapPx(list) : 0;
  if (list) list.remove();

  return { leading, items, itemGap };
}

function packItemPages(
  items: MeasuredItem[],
  gap: number,
  maxPageHeight: number,
  initialLeading: HTMLElement[],
  measureLeading: (blocks: HTMLElement[]) => number
): PdfPagePlan[] {
  const plans: PdfPagePlan[] = [];
  let itemIndex = 0;
  let leading = initialLeading;

  while (itemIndex < items.length) {
    const leadingHeight = measureLeading(leading);
    let used = leadingHeight + (leading.length > 0 ? gap : 0);
    const pageItems: MeasuredItem[] = [];

    while (itemIndex < items.length) {
      const gapBefore = pageItems.length > 0 ? gap : 0;
      const needed = gapBefore + items[itemIndex].height;

      if (pageItems.length > 0 && used + needed > maxPageHeight) break;

      if (pageItems.length === 0 && used + needed > maxPageHeight) {
        if (used > 0) break;
        pageItems.push(items[itemIndex++]);
        break;
      }

      pageItems.push(items[itemIndex++]);
      used += needed;
    }

    if (pageItems.length === 0 && leading.length === 0) break;

    plans.push({ leading, items: pageItems });
    leading = [];
  }

  if (leading.length > 0) {
    plans.push({ leading, items: [] });
  }

  return plans;
}

function renderOccupationPage(width: number, plan: PdfPagePlan): HTMLElement {
  const page = createPageShell(width);
  for (const block of plan.leading) {
    page.appendChild(block);
  }
  if (plan.items.length > 0) {
    const list = document.createElement("ol");
    list.className = "occupation-match-list";
    for (const item of plan.items) {
      list.appendChild(item.element);
    }
    page.appendChild(list);
  }
  return page;
}

function buildOccupationMatchesPages(source: HTMLElement): {
  staging: HTMLElement;
  pages: HTMLElement[];
} {
  const width = source.offsetWidth;
  const staging = document.createElement("div");
  staging.style.cssText = [
    "position:fixed",
    "left:-10000px",
    "top:0",
    `width:${width}px`,
    "pointer-events:none",
  ].join(";");
  document.body.appendChild(staging);

  const working = source.cloneNode(true) as HTMLElement;
  prepareOccupationMatchesCloneForExport(document, working);
  staging.appendChild(working);
  void working.offsetHeight;

  const maxPageHeight = maxSourceHeightPx(width);
  const measureLeading = (blocks: HTMLElement[]) =>
    measureBlocks(staging, width, blocks);
  const { leading, items, itemGap } = parseOccupationExportParts(working);
  working.remove();

  const pagePlans =
    items.length > 0
      ? packItemPages(items, itemGap, maxPageHeight, leading, measureLeading)
      : leading.length > 0
        ? [{ leading, items: [] }]
        : [];

  const pages = pagePlans.map((plan) => renderOccupationPage(width, plan));
  for (const page of pages) {
    staging.appendChild(page);
  }

  return { staging, pages };
}

export async function openOccupationMatchesPdf(element: HTMLElement): Promise<void> {
  const { staging, pages } = buildOccupationMatchesPages(element);

  try {
    await openPackedDomPdf(pages, prepareOccupationMatchesCloneForExport);
  } finally {
    staging.remove();
  }
}
