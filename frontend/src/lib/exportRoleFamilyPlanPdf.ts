import {
  isPdfPageEmpty,
  maxSourceHeightPx,
  openPackedDomPdf,
} from "./exportDomPdf";

function prepareRoleFamilyPlanCloneForExport(_doc: Document, clone: HTMLElement) {
  clone.classList.add("role-family-plan", "role-family-plan--pdf-export");
}

type MeasuredCard = {
  element: HTMLElement;
  height: number;
};

type RoleFamilyExportParts = {
  cards: MeasuredCard[];
  cardGap: number;
  rationale: HTMLElement | null;
};

type PdfPagePlan = {
  cards: MeasuredCard[];
};

function createPageShell(width: number): HTMLElement {
  const page = document.createElement("div");
  page.className = "role-family-plan role-family-plan--pdf-export";
  page.style.width = `${width}px`;
  prepareRoleFamilyPlanCloneForExport(document, page);
  return page;
}

function planGapPx(plan: HTMLElement): number {
  const style = getComputedStyle(plan);
  const gap = parseFloat(style.rowGap || style.gap);
  return Number.isFinite(gap) ? gap : 16;
}

function parseRoleFamilyExportParts(working: HTMLElement): RoleFamilyExportParts {
  const rationale = working.querySelector<HTMLElement>(".aptitude-rationale-section");
  if (rationale) rationale.remove();

  const cards = Array.from(working.querySelectorAll<HTMLElement>(".role-family-card")).map(
    (element) => ({
      element,
      height: element.getBoundingClientRect().height,
    })
  );

  return {
    cards,
    cardGap: planGapPx(working),
    rationale: rationale ?? null,
  };
}

function packCardPages(
  cards: MeasuredCard[],
  gap: number,
  maxPageHeight: number
): PdfPagePlan[] {
  const plans: PdfPagePlan[] = [];
  let cardIndex = 0;

  while (cardIndex < cards.length) {
    let used = 0;
    const pageCards: MeasuredCard[] = [];

    while (cardIndex < cards.length) {
      const gapBefore = pageCards.length > 0 ? gap : 0;
      const needed = gapBefore + cards[cardIndex].height;

      if (pageCards.length > 0 && used + needed > maxPageHeight) break;

      if (pageCards.length === 0 && needed > maxPageHeight) {
        pageCards.push(cards[cardIndex++]);
        break;
      }

      pageCards.push(cards[cardIndex++]);
      used += needed;
    }

    if (pageCards.length === 0) break;
    plans.push({ cards: pageCards });
  }

  return plans;
}

function renderRoleFamilyPage(width: number, plan: PdfPagePlan): HTMLElement {
  const page = createPageShell(width);
  for (const card of plan.cards) {
    page.appendChild(card.element);
  }
  return page;
}

function appendRationale(
  pages: HTMLElement[],
  rationale: HTMLElement,
  maxPageHeight: number,
  width: number
): HTMLElement[] {
  rationale.style.marginTop = "1.25rem";
  const lastPage = pages.at(-1);

  if (lastPage) {
    lastPage.appendChild(rationale);
    void lastPage.offsetHeight;
    if (lastPage.getBoundingClientRect().height <= maxPageHeight) {
      return pages;
    }
    lastPage.removeChild(rationale);
  }

  const rationalePage = createPageShell(width);
  rationalePage.appendChild(rationale);
  return [...pages, rationalePage];
}

function buildRoleFamilyPlanPages(source: HTMLElement): {
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
  prepareRoleFamilyPlanCloneForExport(document, working);
  staging.appendChild(working);
  void working.offsetHeight;

  const maxPageHeight = maxSourceHeightPx(width);
  const { cards, cardGap, rationale } = parseRoleFamilyExportParts(working);
  working.remove();

  let pagePlans: PdfPagePlan[] =
    cards.length > 0 ? packCardPages(cards, cardGap, maxPageHeight) : [];

  let pages = pagePlans.map((plan) => renderRoleFamilyPage(width, plan));
  for (const page of pages) {
    staging.appendChild(page);
  }

  if (rationale && !isPdfPageEmpty(rationale)) {
    const pageCountBefore = pages.length;
    pages = appendRationale(pages, rationale, maxPageHeight, width);
    if (pages.length > pageCountBefore) {
      staging.appendChild(pages.at(-1)!);
    }
  }

  return { staging, pages };
}

export async function openRoleFamilyPlanPdf(element: HTMLElement): Promise<void> {
  const { staging, pages } = buildRoleFamilyPlanPages(element);

  try {
    await openPackedDomPdf(pages, prepareRoleFamilyPlanCloneForExport);
  } finally {
    staging.remove();
  }
}
