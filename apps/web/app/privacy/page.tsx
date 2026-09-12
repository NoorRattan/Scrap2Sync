import Link from "next/link";
export default function PrivacyPage() {
  return (
    <main id="main-content" className="document-shell">
      <Link className="brand" href="/">
        Scrap2Sync
      </Link>
      <h1>Your notes stay in this session.</h1>
      <p>
        Scrap2Sync does not store your notes or drafts in a database, browser
        history, or browser storage. They are held in memory while you use the
        page and the API processes a request.
      </p>
      <h2>External AI processing</h2>
      <p>
        If the operator enables the OpenAI formatter, your notes and selected
        style are sent to OpenAI for processing. Scrap2Sync’s lack of storage
        does not determine the provider’s retention or processing policies.
      </p>
      <p>
        The local configuration disables external AI. It uses conservative rules
        to organize your original wording. Before enabling OpenAI, the operator
        must verify the exact model, processing region, retention and training
        controls, account terms, and verification date. These details have not
        been verified for a live deployment.
      </p>
      <h2>What the browser remembers</h2>
      <p>
        Only your style and visual preferences may be saved on this device. The
        workspace includes Reset preferences. If storage is unavailable, you can
        still generate, edit, and copy your draft.
      </p>
      <h2>Before you submit</h2>
      <p>
        Remove credentials, secrets, or information your workplace restricts.
        Review the draft before copying it. The evaluated language is English;
        other languages are best effort.
      </p>
      <p>
        No account, tracking, analytics, or automatic posting is included.
        Closing or reloading the page clears its notes and draft. Cancelling a
        request prevents its result from replacing your draft; an already-sent
        provider request may still finish.
      </p>
      <Link className="button secondary" href="/">
        Back to the workspace
      </Link>
    </main>
  );
}
