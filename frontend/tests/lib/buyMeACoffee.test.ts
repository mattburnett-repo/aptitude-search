import { afterEach, describe, expect, it, vi } from "vitest";
import {
  bmcButtonConfig,
  renderBuyMeACoffeeButton,
} from "../../src/lib/buyMeACoffee";

describe("renderBuyMeACoffeeButton", () => {
  afterEach(() => {
    delete window.bmcBtnWidget;
    document.getElementById("bmc-button-script")?.remove();
  });

  it("renders button HTML via bmcBtnWidget", async () => {
    window.bmcBtnWidget = vi.fn(
      () => '<a class="bmc-btn">Buy me a coffee</a>',
    );
    const container = document.createElement("div");

    await renderBuyMeACoffeeButton(container, "aptitude.search");

    expect(window.bmcBtnWidget).toHaveBeenCalledWith(
      bmcButtonConfig.text,
      "aptitude.search",
      bmcButtonConfig.color,
      bmcButtonConfig.emoji,
      bmcButtonConfig.font,
      bmcButtonConfig.fontColor,
      bmcButtonConfig.outlineColor,
      bmcButtonConfig.coffeeColor,
    );
    expect(container.innerHTML).toContain("Buy me a coffee");
  });
});
