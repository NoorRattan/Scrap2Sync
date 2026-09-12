"use client";

import { useCallback, useRef, useState } from "react";

export function useGenerationLatency() {
  const start = useRef<number | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const begin = useCallback(() => {
    start.current = performance.now();
    setDuration(null);
  }, []);
  const painted = useCallback(() => {
    if (start.current !== null) {
      setDuration(Math.max(0, Math.round(performance.now() - start.current)));
      start.current = null;
    }
  }, []);
  return { duration, begin, painted };
}
