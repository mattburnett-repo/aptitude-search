import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { bmcButtonConfig } from "../../src/lib/buyMeACoffee";

async function loadSiteChrome() {
  return import("../../src/components/SiteChrome");
}

describe("SiteChrome support links", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
    delete window.bmcBtnWidget;
    document.getElementById("bmc-button-script")?.remove();
    document.querySelector(".site-footer-bmc")?.replaceChildren();
  });

  it("links donations and renders the BMC button when VITE_SUPPORT_URL is set", async () => {
    vi.stubEnv("VITE_SUPPORT_URL", "https://buymeacoffee.com/aptitude.search");
    window.bmcBtnWidget = vi.fn(
      () =>
        '<a href="https://buymeacoffee.com/aptitude.search">Buy me a coffee</a>',
    );
    const { InputTrustNotes, SiteFooter } = await loadSiteChrome();

    render(
      <>
        <InputTrustNotes />
        <SiteFooter />
      </>,
    );

    const donations = screen.getByRole("link", { name: "donations" });
    expect(donations).toHaveAttribute(
      "href",
      "https://buymeacoffee.com/aptitude.search",
    );
    expect(donations).toHaveAttribute("target", "_blank");
    expect(donations).toHaveAttribute("rel", "noopener noreferrer");

    await waitFor(() => {
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
    });

    expect(
      screen.getByRole("link", { name: "Buy me a coffee" }),
    ).toBeInTheDocument();
  });

  it("renders plain text when VITE_SUPPORT_URL is unset", async () => {
    vi.stubEnv("VITE_SUPPORT_URL", "");
    const { InputTrustNotes, SiteFooter } = await loadSiteChrome();

    render(
      <>
        <InputTrustNotes />
        <SiteFooter />
      </>,
    );

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(document.querySelector(".site-footer-bmc")).not.toBeInTheDocument();
    expect(
      screen.getByText(/donations are always appreciated/),
    ).toBeInTheDocument();
  });
});
