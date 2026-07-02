import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

async function loadBuyMeACoffeeButton() {
  return import("../../src/components/BuyMeACoffeeButton");
}

describe("BuyMeACoffeeButton", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("renders a static support link styled like the BMC button", async () => {
    vi.stubEnv("VITE_SUPPORT_URL", "https://buymeacoffee.com/aptitude.search");
    const { BuyMeACoffeeButton } = await loadBuyMeACoffeeButton();

    render(<BuyMeACoffeeButton />);

    const link = screen.getByRole("link", { name: "Buy me a coffee" });
    expect(link).toHaveAttribute(
      "href",
      "https://buymeacoffee.com/aptitude.search",
    );
    expect(link).toHaveClass("bmc-btn");
    expect(link.querySelector(".bmc-btn-text")).toHaveTextContent(
      "Buy me a coffee",
    );
  });

  it("renders nothing when support URL is unset", async () => {
    vi.stubEnv("VITE_SUPPORT_URL", "");
    const { BuyMeACoffeeButton } = await loadBuyMeACoffeeButton();

    const { container } = render(<BuyMeACoffeeButton />);

    expect(container).toBeEmptyDOMElement();
  });
});
