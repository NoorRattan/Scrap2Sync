"use client";

import { useEffect, useRef } from "react";
import { ApiError } from "@/lib/apiClient";
import type { GenerationState } from "@/hooks/useGenerate";
import { Icon } from "./ui/Icon";

export function GenerationStatus({
  state,
  error,
  announcement,
  retrySeconds,
}: {
  state: GenerationState;
  error: ApiError | null;
  announcement: string;
  retrySeconds: number;
}) {
  const summary = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (error) summary.current?.focus();
  }, [error]);
  const messages: Record<GenerationState, string> = {
    idle: "",
    generating: "Organizing your notes. Your current draft stays here.",
    success: "Your draft is ready. Review it before copying.",
    fallback:
      "Your draft is ready in rules mode. Review the wording and sections before copying.",
    error: "",
    cancelled:
      "Request cancelled. An already-sent AI request may still finish, but its result will be ignored.",
  };
  return (
    <>
      <div
        className="live-status"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {announcement || messages[state]}
      </div>
      {error && (
        <div className="error-summary" ref={summary} tabIndex={-1} role="alert">
          <div className="status-title">
            <Icon name="warning" />
            <strong>We couldn’t finish this request</strong>
          </div>
          <p>{error.message}</p>
          {retrySeconds > 0 ? (
            <p>
              Try again in {retrySeconds}{" "}
              {retrySeconds === 1 ? "second" : "seconds"}.
            </p>
          ) : (
            <p>
              Your notes and any existing draft are still here. Submit again
              when you’re ready.
            </p>
          )}
          {error.requestId && (
            <p className="support-id">Support reference: {error.requestId}</p>
          )}
        </div>
      )}
    </>
  );
}
