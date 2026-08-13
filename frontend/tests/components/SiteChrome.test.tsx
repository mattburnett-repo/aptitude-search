import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

async function loadSiteChrome() {
  return import("../../src/components/SiteChrome");
}

describe("SiteChrome support links", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("matches footer markup snapshot", async () => {
    vi.stubEnv("VITE_SUPPORT_URL", "");
    const { SiteFooter } = await loadSiteChrome();

    const { container } = render(<SiteFooter />);
    expect(container.querySelector(".site-footer")).toMatchSnapshot();
  });

  it("links donations and renders the BMC button when VITE_SUPPORT_URL is set", async () => {
    vi.stubEnv("VITE_SUPPORT_URL", "https://buymeacoffee.com/aptitude.search");
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

    const bmcButton = screen.getByRole("link", { name: "Buy me a coffee" });
    expect(bmcButton).toHaveAttribute(
      "href",
      "https://buymeacoffee.com/aptitude.search",
    );
    expect(bmcButton).toHaveClass("bmc-btn");
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
