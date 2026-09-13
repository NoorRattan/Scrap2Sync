"use client";

import {
  LazyMotion,
  domAnimation,
  MotionConfig,
  m,
  useAnimationControls,
  useReducedMotion,
} from "framer-motion";
import { ArrowDown, ArrowUpRight, Command, ShieldCheck } from "lucide-react";
import { useEffect, type ReactNode } from "react";
import { SyncOrbSlot } from "./SyncOrbSlot";

export function Experience({
  children,
  reducedMotion,
}: {
  children: ReactNode;
  reducedMotion: boolean;
}) {
  useEffect(() => {
    const media = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (
      !media ||
      reducedMotion ||
      media.matches ||
      !("ResizeObserver" in window)
    )
      return;
    let disposed = false;
    let cleanup: (() => void) | undefined;
    const timer = window.setTimeout(() => {
      void Promise.all([
        import("lenis"),
        import("gsap"),
        import("gsap/ScrollTrigger"),
      ])
        .then(([{ default: Lenis }, { gsap }, { ScrollTrigger }]) => {
          if (disposed) return;
          gsap.registerPlugin(ScrollTrigger);
          const lenis = new Lenis({
            autoRaf: true,
            duration: 0.85,
            anchors: true,
            prevent: (node) =>
              node.matches(
                "textarea, select, [role='dialog'], [data-lenis-prevent]",
              ),
          });
          lenis.on("scroll", ScrollTrigger.update);
          const context = gsap.context(() => {
            gsap.utils
              .toArray<HTMLElement>(".process-step")
              .forEach((element) => {
                gsap.from(element, {
                  y: 28,
                  duration: 0.9,
                  ease: "power3.out",
                  scrollTrigger: {
                    trigger: element,
                    start: "top 92%",
                    once: true,
                  },
                });
              });
          });
          cleanup = () => {
            context.revert();
            lenis.destroy();
          };
        })
        .catch(() => {
          cleanup?.();
        });
    }, 1000);
    const stop = () => {
      disposed = true;
      window.clearTimeout(timer);
      cleanup?.();
    };
    media.addEventListener("change", stop);
    return () => {
      stop();
      media.removeEventListener("change", stop);
    };
  }, [reducedMotion]);

  return (
    <LazyMotion features={domAnimation}>
      <MotionConfig
        reducedMotion={reducedMotion ? "always" : "user"}
        transition={{ type: "spring", stiffness: 260, damping: 24 }}
      >
        <div className="experience" data-reduced-motion={reducedMotion}>
          {children}
        </div>
      </MotionConfig>
    </LazyMotion>
  );
}

export function Hero({ reducedMotion }: { reducedMotion: boolean }) {
  const magnetic = useAnimationControls();
  const systemReduced = useReducedMotion();
  return (
    <section className="hero" aria-labelledby="workspace-title">
      <div className="hero-copy">
        <p className="eyebrow">
          <span className="status-dot" /> A CLEARER WAY TO START YOUR DAY
        </p>
        <h1 id="workspace-title">
          <span>Less noise.</span>
          <span>
            More <em>signal.</em>
          </span>
        </h1>
        <p className="hero-description">
          Your thoughts, all over the place.
          <br />
          Your next standup, beautifully together.
        </p>
        <div className="hero-actions">
          <m.a
            href="#workspace"
            className="button primary hero-cta"
            animate={magnetic}
            onPointerMove={(event) => {
              if (
                reducedMotion ||
                systemReduced ||
                event.pointerType !== "mouse"
              )
                return;
              const bounds = event.currentTarget.getBoundingClientRect();
              void magnetic.start({
                x: (event.clientX - bounds.left - bounds.width / 2) * 0.07,
                y: (event.clientY - bounds.top - bounds.height / 2) * 0.12,
              });
            }}
            onPointerLeave={() => {
              void magnetic.start({ x: 0, y: 0 });
            }}
            whileTap={{ scale: 0.97 }}
          >
            Find your clarity <ArrowUpRight size={18} />
          </m.a>
          <span className="hero-assurance">
            <ShieldCheck size={14} /> No account. Just your words.
          </span>
        </div>
      </div>
      <div className="hero-art">
        <div className="scene-grid" aria-hidden="true" />
        <div className="scene-orbit orbit-one" aria-hidden="true" />
        <div className="scene-orbit orbit-two" aria-hidden="true" />
        <SyncOrbSlot reducedMotion={reducedMotion} />
        <div className="scene-coordinate coordinate-top" aria-hidden="true">
          <span>FIG. 01</span> CLARITY IN MOTION
        </div>
        <div className="scene-coordinate coordinate-bottom" aria-hidden="true">
          <span className="status-dot" /> SCATTERED → SYNCHRONIZED
        </div>
        <div className="scene-note note-before" aria-hidden="true">
          <span className="note-pin" />a thousand thoughts
          <span className="note-lines">
            <i />
            <i />
            <i />
          </span>
        </div>
        <div className="scene-note note-after" aria-hidden="true">
          <span className="note-check">↗</span>one clear update
        </div>
        <span className="scene-cross cross-one" aria-hidden="true">
          +
        </span>
        <span className="scene-cross cross-two" aria-hidden="true">
          +
        </span>
      </div>
      <div className="hero-baseline">
        <span>BUILT FOR THE MOMENT BEFORE THE MEETING</span>
        <a href="#workspace">
          ENTER THE WORKSPACE <ArrowDown size={13} />
        </a>
        <span className="baseline-index">[ 001 — 003 ]</span>
      </div>
    </section>
  );
}

export function Process() {
  return (
    <section className="process" id="process" aria-labelledby="process-title">
      <div className="process-intro">
        <p className="eyebrow">A SMALL RITUAL. A LIGHTER DAY.</p>
        <h2 id="process-title">
          From scattered
          <br />
          to <em>in sync.</em>
        </h2>
        <p>
          Less time finding the words.
          <br />
          More time doing the work.
        </p>
      </div>
      <div className="process-list">
        <article className="process-step">
          <span>01</span>
          <div>
            <h3>Let it all out.</h3>
            <p>
              Paste your rough notes. What shipped, what’s next, what’s in the
              way. One thought per line works best.
            </p>
          </div>
          <Command size={20} />
        </article>
        <article className="process-step">
          <span>02</span>
          <div>
            <h3>Give it a little structure.</h3>
            <p>
              Choose your style. Turn those loose ends into Yesterday, Today,
              and Blockers.
            </p>
          </div>
          <span className="process-glyph" aria-hidden="true">
            ≋
          </span>
        </article>
        <article className="process-step">
          <span>03</span>
          <div>
            <h3>Make it yours. Then go.</h3>
            <p>
              Review, edit, and copy. Your voice stays yours. Your team gets the
              clear version.
            </p>
          </div>
          <ArrowUpRight size={22} />
        </article>
      </div>
    </section>
  );
}
