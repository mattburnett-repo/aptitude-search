import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import App from "../src/App";

describe("App", () => {
  it("renders the main shell with Go disabled until resume input exists", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Aptitude Search" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Go" })).toBeDisabled();
  });

  it("enables Go after pasting resume text", async () => {
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByRole("button", { name: "Paste resume" }));
    await user.type(
      screen.getByPlaceholderText("Paste resume text..."),
      "Alex Morgan — software engineer"
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Go" })).toBeEnabled();
    });
  });
});
