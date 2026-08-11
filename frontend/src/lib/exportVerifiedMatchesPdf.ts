import {
  isPdfPageEmpty,
  maxSourceHeightPx,
  openPackedDomPdf,
} from "./exportDomPdf";

function prepareVerifiedMatchesCloneForExport(_doc: Document, clone: HTMLElement) {
  clone.classList.add("verified-matches", "verified-matches--pdf-export");
  for (const node of clone.querySelectorAll("details")) {
    if (node instanceof HTMLDetailsElement) {
      node.open = true;
    }
  }
}

type MeasuredCard = {
  element: HTMLElement;
  height: number;
};

type VerifiedExportParts = {
  leading: HTMLElement[];
  cards: MeasuredCard[];
  cardGap: number;
  notes: HTMLElement | null;
};

type PdfPagePlan = {
  leading: HTMLElement[];
  cards: MeasuredCard[];
};

function createPageShell(width: number): HTMLElement {
  const page = document.createElement("div");
  page.className = "verified-matches";
  page.style.width = `${width}px`;
  prepareVerifiedMatchesCloneForExport(document, page);
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

function listGapPx(list: HTMLElement): number {
  const style = getComputedStyle(list);
  const gap = parseFloat(style.rowGap || style.gap);
  return Number.isFinite(gap) ? gap : 12;
}

function parseVerifiedExportParts(working: HTMLElement): VerifiedExportParts {
  const searchSection = working
    .querySelector(".verified-search-plan")
    ?.closest<HTMLElement>(".verified-section");
  if (searchSection) searchSection.remove();

  const notesSection = working
    .querySelector(".verified-notes")
    ?.closest<HTMLElement>(".verified-section");
  if (notesSection) notesSection.remove();

  const leading: HTMLElement[] = [];
  if (searchSection && !isPdfPageEmpty(searchSection)) {
    leading.push(searchSection);
  }

  const resultsSection = working
    .querySelector(".job-card-list")
    ?.closest<HTMLElement>(".verified-section");

  let cards: MeasuredCard[] = [];
  let cardGap = 12;

  if (resultsSection) {
    const list = resultsSection.querySelector<HTMLElement>(".job-card-list");
    if (list) {
      cards = Array.from(list.querySelectorAll<HTMLElement>(".job-card")).map(
        (element) => ({
          element,
          height: element.getBoundingClientRect().height,
        })
      );
      cardGap = listGapPx(list);
    }

    const header = document.createElement("div");
    header.className = "verified-results-header";
    for (const child of Array.from(resultsSection.children)) {
      if (child === list) continue;
      header.appendChild(child);
    }
    resultsSection.remove();

    if (header.childNodes.length > 0) {
      leading.push(header);
    }
  }

  return { leading, cards, cardGap, notes: notesSection ?? null };
}

function packCardPages(
  cards: MeasuredCard[],
  gap: number,
  maxPageHeight: number,
  initialLeading: HTMLElement[],
  measureLeading: (blocks: HTMLElement[]) => number
): PdfPagePlan[] {
  const plans: PdfPagePlan[] = [];
  let cardIndex = 0;
  let leading = initialLeading;

  while (cardIndex < cards.length) {
    const leadingHeight = measureLeading(leading);
    let used = leadingHeight + (leading.length > 0 ? gap : 0);
    const pageCards: MeasuredCard[] = [];

    while (cardIndex < cards.length) {
      const gapBefore = pageCards.length > 0 ? gap : 0;
      const needed = gapBefore + cards[cardIndex].height;

      if (pageCards.length > 0 && used + needed > maxPageHeight) break;

      if (pageCards.length === 0 && used + needed > maxPageHeight) {
        if (used > 0) break;
        pageCards.push(cards[cardIndex++]);
        break;
      }

      pageCards.push(cards[cardIndex++]);
      used += needed;
    }

    if (pageCards.length === 0 && leading.length === 0) break;

    plans.push({ leading, cards: pageCards });
    leading = [];
  }

  if (leading.length > 0) {
    plans.push({ leading, cards: [] });
  }

  return plans;
}

function renderVerifiedPage(
  width: number,
  plan: PdfPagePlan
): HTMLElement {
  const page = createPageShell(width);
  for (const block of plan.leading) {
    page.appendChild(block);
  }
  if (plan.cards.length > 0) {
    const cardList = document.createElement("div");
    cardList.className = "job-card-list";
    for (const card of plan.cards) {
      cardList.appendChild(card.element);
    }
    page.appendChild(cardList);
  }
  return page;
}

function appendNotes(
  pages: HTMLElement[],
  notes: HTMLElement,
  maxPageHeight: number,
  width: number
): HTMLElement[] {
  notes.style.marginTop = "1.25rem";
  const lastPage = pages.at(-1);

  if (lastPage) {
    lastPage.appendChild(notes);
    void lastPage.offsetHeight;
    if (lastPage.getBoundingClientRect().height <= maxPageHeight) {
      return pages;
    }
    lastPage.removeChild(notes);
  }

  const notesPage = createPageShell(width);
  notesPage.appendChild(notes);
  return [...pages, notesPage];
}

function buildVerifiedMatchesPages(source: HTMLElement): {
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
  prepareVerifiedMatchesCloneForExport(document, working);
  staging.appendChild(working);
  void working.offsetHeight;

  const maxPageHeight = maxSourceHeightPx(width);
  const measureLeading = (blocks: HTMLElement[]) =>
    measureBlocks(staging, width, blocks);
  const { leading, cards, cardGap, notes } = parseVerifiedExportParts(working);
  working.remove();

  let pagePlans: PdfPagePlan[] =
    cards.length > 0
      ? packCardPages(cards, cardGap, maxPageHeight, leading, measureLeading)
      : leading.length > 0
        ? [{ leading, cards: [] }]
        : [];

  let pages = pagePlans.map((plan) => renderVerifiedPage(width, plan));
  for (const page of pages) {
    staging.appendChild(page);
  }

  if (notes && !isPdfPageEmpty(notes)) {
    const pageCountBefore = pages.length;
    pages = appendNotes(pages, notes, maxPageHeight, width);
    if (pages.length > pageCountBefore) {
      staging.appendChild(pages.at(-1)!);
    }
  }

  return { staging, pages };
}

export async function openVerifiedMatchesPdf(element: HTMLElement): Promise<void> {
  const { staging, pages } = buildVerifiedMatchesPages(element);

  try {
    await openPackedDomPdf(pages, prepareVerifiedMatchesCloneForExport);
  } finally {
    staging.remove();
  }
}
