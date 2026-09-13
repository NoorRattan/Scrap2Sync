"use client";

import dynamic from "next/dynamic";
import { Component, useEffect, useRef, useState, type ReactNode } from "react";
import { Box, Pause } from "lucide-react";

const LazySyncOrb = dynamic(
  () => import("./SyncOrb").then((module) => module.SyncOrb),
  { ssr: false },
);

function supportsWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(
      canvas.getContext("webgl2", { failIfMajorPerformanceCaveat: true }) ??
      canvas.getContext("webgl", { failIfMajorPerformanceCaveat: true }),
    );
  } catch {
    return false;
  }
}

class SceneBoundary extends Component<
  { children: ReactNode; onFailure: () => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onFailure();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

export function SyncOrbSlot({ reducedMotion }: { reducedMotion: boolean }) {
  const host = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const [systemReduced, setSystemReduced] = useState(false);
  const [interactive, setInteractive] = useState(false);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    const media = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!media) return;
    const update = () => setSystemReduced(media.matches);
    const timer = window.setTimeout(update, 0);
    media.addEventListener("change", update);
    return () => {
      window.clearTimeout(timer);
      media.removeEventListener("change", update);
    };
  }, []);

  useEffect(() => {
    if (!("IntersectionObserver" in window)) {
      const timer = setTimeout(() => setVisible(true), 0);
      return () => clearTimeout(timer);
    }
    const observer = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { rootMargin: "120px" },
    );
    if (host.current) observer.observe(host.current);
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <div ref={host} className="sync-orb" aria-hidden="true">
        <div className="sculpture-fallback" />
        {visible && interactive && !unavailable && (
          <SceneBoundary
            onFailure={() => {
              setUnavailable(true);
              setInteractive(false);
            }}
          >
            <LazySyncOrb reducedMotion={reducedMotion || systemReduced} />
          </SceneBoundary>
        )}
      </div>
      {process.env.NEXT_PUBLIC_ENABLE_SYNC_ORB !== "false" && (
        <button
          type="button"
          className="scene-toggle"
          aria-pressed={interactive}
          disabled={unavailable}
          onClick={() => {
            if (interactive) {
              setInteractive(false);
              return;
            }
            if (!supportsWebGL()) {
              setUnavailable(true);
              return;
            }
            setInteractive(true);
          }}
        >
          {interactive ? <Pause size={11} /> : <Box size={11} />}
          {unavailable
            ? "3D unavailable on this device"
            : interactive
              ? "Pause 3D"
              : "Explore in 3D"}
        </button>
      )}
    </>
  );
}
