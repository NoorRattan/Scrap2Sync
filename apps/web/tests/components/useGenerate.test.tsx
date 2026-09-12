import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useGenerate } from "@/hooks/useGenerate";
import { ApiError, generateDraft } from "@/lib/apiClient";
import { DEFAULT_PROFILE } from "@/lib/profiles";
import type { GenerateRequest, GenerateResponse } from "@/lib/types";
import { result } from "../fixtures";

vi.mock("@/lib/apiClient", async (original) => ({
  ...(await original<typeof import("@/lib/apiClient")>()),
  generateDraft: vi.fn(),
}));
const generateMock = vi.mocked(generateDraft);
beforeEach(() => {
  generateMock.mockReset();
});

describe("request ownership and cancellation", () => {
  it("allows one active request and ignores a cancelled response arriving after its replacement", async () => {
    const requests: {
      request: GenerateRequest;
      resolve: (response: GenerateResponse) => void;
    }[] = [];
    generateMock.mockImplementation(
      (request) =>
        new Promise((resolve) => requests.push({ request, resolve })),
    );
    const hook = renderHook(() => useGenerate());
    act(() => {
      void hook.result.current.generate("first", DEFAULT_PROFILE);
      void hook.result.current.generate("duplicate", DEFAULT_PROFILE);
    });
    expect(requests).toHaveLength(1);
    act(() => hook.result.current.cancel());
    act(() => {
      void hook.result.current.generate("second", DEFAULT_PROFILE);
    });
    expect(requests).toHaveLength(2);
    await act(async () =>
      requests[1].resolve(result(requests[1].request.clientRequestId)),
    );
    expect(hook.result.current.response?.clientRequestId).toBe(
      requests[1].request.clientRequestId,
    );
    await act(async () =>
      requests[0].resolve(result(requests[0].request.clientRequestId)),
    );
    expect(hook.result.current.response?.clientRequestId).toBe(
      requests[1].request.clientRequestId,
    );
  });
  it("aborts on unmount and respects Retry-After without a hidden retry", async () => {
    generateMock.mockRejectedValue(
      new ApiError("Wait", 429, null, {}, Date.now() + 60_000),
    );
    const hook = renderHook(() => useGenerate());
    act(() => {
      void hook.result.current.generate("notes", DEFAULT_PROFILE);
    });
    await waitFor(() => expect(hook.result.current.state).toBe("error"));
    act(() => {
      void hook.result.current.generate("notes", DEFAULT_PROFILE);
    });
    expect(generateMock).toHaveBeenCalledTimes(1);
    hook.unmount();
    generateMock.mockImplementation(() => new Promise(() => {}));
    const pending = renderHook(() => useGenerate());
    act(() => {
      void pending.result.current.generate("notes", DEFAULT_PROFILE);
    });
    const signal = generateMock.mock.calls[1][1];
    pending.unmount();
    expect(signal.aborted).toBe(true);
  });
});
