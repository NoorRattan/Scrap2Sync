"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, generateDraft } from "@/lib/apiClient";
import { normalizeNotes } from "@/lib/profiles";
import type { GenerateResponse, StyleProfile } from "@/lib/types";
import { useGenerationLatency } from "./useGenerationLatency";

export type GenerationState =
  "idle" | "generating" | "success" | "fallback" | "error" | "cancelled";

export function useGenerate() {
  const [state, setState] = useState<GenerationState>("idle");
  const [response, setResponse] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const active = useRef<{ id: string; controller: AbortController } | null>(
    null,
  );
  const mounted = useRef(true);
  const { duration, begin, painted } = useGenerationLatency();
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      active.current?.controller.abort();
      active.current = null;
    };
  }, []);
  useEffect(() => {
    if (!response) return;
    let second = 0;
    const first = requestAnimationFrame(() => {
      second = requestAnimationFrame(painted);
    });
    return () => {
      cancelAnimationFrame(first);
      cancelAnimationFrame(second);
    };
  }, [response, painted]);

  const generate = useCallback(
    async (rawNotes: string, styleProfile: StyleProfile) => {
      if (active.current || (error?.retryAt && Date.now() < error.retryAt))
        return;
      const id = crypto.randomUUID();
      const controller = new AbortController();
      active.current = { id, controller };
      setState("generating");
      setError(null);
      begin();
      try {
        const result = await generateDraft(
          {
            rawNotes: normalizeNotes(rawNotes),
            styleProfile,
            clientRequestId: id,
          },
          controller.signal,
        );
        if (!mounted.current || active.current?.id !== id) return;
        if (result.clientRequestId !== id)
          throw new ApiError(
            "The response did not match this request. Your existing draft has been kept.",
          );
        setResponse(result);
        setState(
          result.engineVersion === "rules-fallback-v1" ? "fallback" : "success",
        );
      } catch (failure) {
        if (
          !mounted.current ||
          active.current?.id !== id ||
          controller.signal.aborted
        )
          return;
        setError(
          failure instanceof ApiError
            ? failure
            : new ApiError(
                "Could not reach the formatter. Check your connection and try again.",
              ),
        );
        setState("error");
      } finally {
        if (active.current?.id === id) active.current = null;
      }
    },
    [error, begin],
  );

  const cancel = useCallback(() => {
    active.current?.controller.abort();
    active.current = null;
    setState("cancelled");
  }, []);
  const clearValidationError = useCallback(() => {
    if (error?.status === 422) {
      setError(null);
      setState(
        response
          ? response.engineVersion === "rules-fallback-v1"
            ? "fallback"
            : "success"
          : "idle",
      );
    }
  }, [error, response]);
  return {
    state,
    response,
    error,
    generate,
    cancel,
    clearValidationError,
    clientDurationMs: duration,
  };
}
