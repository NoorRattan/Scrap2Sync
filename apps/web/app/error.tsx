"use client";
import Link from "next/link";

export default function PageError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main id="main-content" className="document-shell">
      <Link className="brand" href="/">
        Scrap2Sync
      </Link>
      <h1>This page could not be shown.</h1>
      <p>
        Try opening the workspace again. Your notes are not saved between page
        loads.
      </p>
      <button className="button primary" onClick={reset}>
        Try again
      </button>
    </main>
  );
}
