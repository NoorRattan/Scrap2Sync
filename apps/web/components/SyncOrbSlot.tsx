"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

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

export function SyncOrbSlot({ reducedMotion }: { reducedMotion: boolean }) {
  const host = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (
      process.env.NEXT_PUBLIC_ENABLE_SYNC_ORB === "false" ||
      !supportsWebGL()
    ) {
      return;
    }
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
    <div ref={host} className="sync-orb" aria-hidden="true">
      {visible && <LazySyncOrb reducedMotion={reducedMotion} />}
    </div>
  );
}
