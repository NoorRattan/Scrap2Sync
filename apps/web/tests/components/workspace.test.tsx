import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Workspace } from "@/components/Workspace";
import { generateDraft, getPrimaryStatus } from "@/lib/apiClient";
import { resetPreferences } from "@/lib/localPreferences";
import { result } from "../fixtures";

vi.mock("@/lib/apiClient", async (original) => ({
  ...(await original<typeof import("@/lib/apiClient")>()),
  generateDraft: vi.fn(),
  getPrimaryStatus: vi.fn(),
}));
beforeEach(() => {
  resetPreferences();
  vi.mocked(generateDraft)
    .mockReset()
    .mockImplementation(async (request) => result(request.clientRequestId));
  vi.mocked(getPrimaryStatus).mockResolvedValue("unconfigured");
});

async function generatedWorkspace() {
  const user = userEvent.setup();
  render(<Workspace />);
  await user.type(
    screen.getByRole("textbox", { name: "Rough notes" }),
    "Finished AX-14. Plan to verify v2.4.",
  );
  await user.click(screen.getByRole("button", { name: "Generate draft" }));
  await screen.findByRole("textbox", { name: "Yesterday item 1" });
  return user;
}

describe("complete editable workspace", () => {
  it("starts with a labelled empty flow, truthful privacy, and no fake draft", async () => {
    render(<Workspace />);
    expect(
      screen.getByRole("button", { name: "Generate draft" }),
    ).toBeDisabled();
    expect(
      screen.queryByRole("textbox", { name: "Yesterday item 1" }),
    ).not.toBeInTheDocument();
    await screen.findByText(/External AI is disabled/);
    expect(screen.getByText(/Evaluated for English/)).toBeInTheDocument();
  });
  it("keeps stable IDs and targeted warnings when edited items move, then copies current text only", async () => {
    const user = await generatedWorkspace();
    const write = vi
      .spyOn(navigator.clipboard, "writeText")
      .mockResolvedValue();
    await user.clear(screen.getByRole("textbox", { name: "Today item 1" }));
    await user.type(
      screen.getByRole("textbox", { name: "Today item 1" }),
      "User changed <Button disabled>",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Move Today item 1 to" }),
      "yesterday",
    );
    const moved = screen.getByRole("textbox", { name: "Yesterday item 2" });
    expect(moved.closest("[data-item-id]")).toHaveAttribute(
      "data-item-id",
      "D002",
    );
    expect(moved).toHaveAccessibleDescription(
      "Review the section for this source note.",
    );
    expect(document.querySelector("Button[disabled]")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Copy All" }));
    expect(write).toHaveBeenCalledWith(
      "Yesterday\n- Finished AX-14.\n- User changed <Button disabled>\n\nToday\n- Not specified.\n\nBlockers\n- No blockers stated.",
    );
    expect(screen.getByText("Complete update copied.")).toBeInTheDocument();
  });
  it("protects manual edits with keep and replace branches and supports add/delete", async () => {
    const user = await generatedWorkspace();
    await user.click(
      screen.getByRole("button", { name: "Add item to Blockers" }),
    );
    await user.type(
      screen.getByRole("textbox", { name: "Blockers item 1" }),
      "My own blocker",
    );
    await user.click(screen.getByRole("button", { name: "Regenerate draft" }));
    expect(
      screen.getByRole("dialog", { name: "Replace your edited draft?" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Keep my edits" }));
    expect(generateDraft).toHaveBeenCalledTimes(1);
    expect(
      screen.getByRole("textbox", { name: "Blockers item 1" }),
    ).toHaveValue("My own blocker");
    await user.click(
      screen.getByRole("button", { name: "Delete Blockers item 1" }),
    );
    expect(
      screen.queryByRole("textbox", { name: "Blockers item 1" }),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Regenerate draft" }));
    await user.click(
      screen.getByRole("button", { name: "Replace and generate" }),
    );
    await waitFor(() => expect(generateDraft).toHaveBeenCalledTimes(2));
  });
  it("reveals selected plain text if clipboard access fails and works with unavailable storage", async () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const user = await generatedWorkspace();
    vi.spyOn(navigator.clipboard, "writeText").mockRejectedValue(
      new Error("blocked"),
    );
    await user.click(screen.getByRole("button", { name: "Copy All" }));
    const fallback = await screen.findByRole("textbox", {
      name: "Plain-text copy fallback",
    });
    expect(fallback).toHaveFocus();
    expect((fallback as HTMLTextAreaElement).selectionEnd).toBe(
      (fallback as HTMLTextAreaElement).value.length,
    );
    await user.click(screen.getByRole("button", { name: "Reset preferences" }));
    expect(
      screen.getByRole("textbox", { name: "Yesterday item 1" }),
    ).toHaveValue("Finished AX-14.");
  });
  it("preserves 10,000 Unicode characters and supports the keyboard shortcut", async () => {
    render(<Workspace />);
    const notes = screen.getByRole("textbox", { name: "Rough notes" });
    fireEvent.change(notes, { target: { value: "😀".repeat(10_000) } });
    expect(screen.getByText("10,000 / 10,000")).toBeInTheDocument();
    fireEvent.keyDown(notes, { key: "Enter", ctrlKey: true });
    await waitFor(() => expect(generateDraft).toHaveBeenCalledOnce());
  });
});
