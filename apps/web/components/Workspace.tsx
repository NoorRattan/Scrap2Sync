"use client";

import * as Dialog from "@radix-ui/react-dialog";
import Link from "next/link";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { ArrowDown, ArrowUpRight, FileText, Layers3, Plus } from "lucide-react";
import { Experience, Hero, Process } from "./Experience";
import { getPrimaryStatus } from "@/lib/apiClient";
import { copyAll, copySection, draftEditError } from "@/lib/copyFormat";
import {
  getPreferences,
  getServerPreferences,
  resetPreferences,
  savePreferences,
  subscribePreferences,
} from "@/lib/localPreferences";
import { normalizeNotes, notesError, profileErrors } from "@/lib/profiles";
import {
  SECTIONS,
  type LocalDraft,
  type PrimaryStatus,
  type Section,
  type StyleProfile,
} from "@/lib/types";
import { useGenerate } from "@/hooks/useGenerate";
import { GenerationStatus } from "./GenerationStatus";
import { NotesInput } from "./NotesInput";
import { StandupDraft } from "./StandupDraft";
import { StyleProfileControl } from "./StyleProfileControl";
import { Icon } from "./ui/Icon";

export function Workspace() {
  const preferences = useSyncExternalStore(
    subscribePreferences,
    getPreferences,
    getServerPreferences,
  );
  const [profileOverride, setProfileOverride] = useState<StyleProfile | null>(
    null,
  );
  const profile = profileOverride ?? preferences.profile;
  const [notes, setNotes] = useState("");
  const [primaryStatus, setPrimaryStatus] = useState<PrimaryStatus | "unknown">(
    "unknown",
  );
  const [localEdits, setLocalEdits] = useState<{
    request: string;
    draft: LocalDraft;
  } | null>(null);
  const [confirmReplace, setConfirmReplace] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const [manualCopy, setManualCopy] = useState<string | null>(null);
  const [now, setNow] = useState(0);
  const generateButton = useRef<HTMLButtonElement>(null);
  const manualCopyField = useRef<HTMLTextAreaElement>(null);
  const generation = useGenerate();
  const busy = generation.state === "generating";
  const response = generation.response;
  const dirty = !!response && localEdits?.request === response.clientRequestId;
  const draft: LocalDraft | null = response
    ? dirty && localEdits
      ? localEdits.draft
      : response.draft
    : null;
  const editError = draft ? draftEditError(draft) : null;
  const localNotesError = notes ? notesError(notes) : null;
  const fields = {
    ...profileErrors(profile),
    ...generation.error?.fieldErrors,
  };
  const noteErrors = localNotesError
    ? [localNotesError]
    : (fields.rawNotes ?? []);
  const retrySeconds = generation.error?.retryAt
    ? Math.max(0, Math.ceil((generation.error.retryAt - now) / 1000))
    : 0;

  useEffect(() => {
    const controller = new AbortController();
    void getPrimaryStatus(controller.signal).then((status) => {
      if (!controller.signal.aborted) setPrimaryStatus(status);
    });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    if (!generation.error?.retryAt) return;
    const timer = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(timer);
  }, [generation.error]);
  useEffect(() => {
    if (manualCopy !== null) {
      manualCopyField.current?.focus();
      manualCopyField.current?.select();
    }
  }, [manualCopy]);

  function updateProfile(next: StyleProfile) {
    setProfileOverride(next);
    generation.clearValidationError();
    setAnnouncement("");
    savePreferences({ ...preferences, profile: next });
  }
  function submit() {
    if (
      busy ||
      retrySeconds > 0 ||
      notesError(notes) ||
      Object.keys(profileErrors(profile)).length
    )
      return;
    setAnnouncement("");
    if (dirty) setConfirmReplace(true);
    else void generation.generate(notes, profile);
  }
  function changeDraft(next: LocalDraft) {
    if (response)
      setLocalEdits({ request: response.clientRequestId, draft: next });
  }
  function editItem(id: string, text: string) {
    if (!draft) return;
    changeDraft(
      Object.fromEntries(
        SECTIONS.map((section) => [
          section,
          draft[section].map((item) =>
            item.itemId === id ? { ...item, text, userEdited: true } : item,
          ),
        ]),
      ) as LocalDraft,
    );
  }
  function moveItem(id: string, target: Section) {
    if (!draft) return;
    const item = SECTIONS.flatMap((section) => draft[section]).find(
      (item) => item.itemId === id,
    );
    if (!item) return;
    const next = Object.fromEntries(
      SECTIONS.map((section) => [
        section,
        draft[section].filter((item) => item.itemId !== id),
      ]),
    ) as LocalDraft;
    next[target] = [...next[target], { ...item, userEdited: true }];
    changeDraft(next);
    setAnnouncement(`Item moved to ${profile.headers[target]}.`);
    requestAnimationFrame(() => document.getElementById(`item-${id}`)?.focus());
  }
  function deleteItem(id: string) {
    if (!draft) return;
    changeDraft(
      Object.fromEntries(
        SECTIONS.map((section) => [
          section,
          draft[section].filter((item) => item.itemId !== id),
        ]),
      ) as LocalDraft,
    );
    setAnnouncement("Item deleted from your draft.");
  }
  function addItem(section: Section) {
    if (!draft) return;
    const id = `local-${crypto.randomUUID()}`;
    changeDraft({
      ...draft,
      [section]: [
        ...draft[section],
        { itemId: id, text: "", sourceFragmentIds: [], userEdited: true },
      ],
    });
    setAnnouncement(`New item added to ${profile.headers[section]}.`);
    requestAnimationFrame(() => document.getElementById(`item-${id}`)?.focus());
  }
  async function copy(section?: Section) {
    if (!draft || editError) return;
    const text = section
      ? copySection(draft, profile, section)
      : copyAll(draft, profile);
    try {
      await navigator.clipboard.writeText(text);
      setAnnouncement(
        section
          ? `${profile.headers[section]} copied.`
          : "Complete update copied.",
      );
      setManualCopy(null);
    } catch {
      setManualCopy(text);
      setAnnouncement(
        "Clipboard access was unavailable. The plain-text update is selected for manual copying.",
      );
    }
  }
  const globalWarnings =
    response?.warnings.filter(
      (warning) =>
        !warning.itemId ||
        !draft ||
        !SECTIONS.some((section) =>
          draft[section].some((item) => item.itemId === warning.itemId),
        ),
    ) ?? [];
  const rulesMode = primaryStatus === "unconfigured";

  return (
    <Experience reducedMotion={preferences.reducedMotion}>
      <div className="app-shell">
        <header className="site-header">
          <Link className="brand" href="/" aria-label="Scrap2Sync home">
            <span className="brand-mark" aria-hidden="true">
              <Layers3 size={23} strokeWidth={1.6} />
            </span>
            Scrap<span className="brand-number">2</span>Sync
          </Link>
          <nav aria-label="Main navigation">
            <a href="#workspace" className="nav-workspace">
              Workspace
            </a>
            <a href="#process" className="nav-process">
              The process
            </a>
            <Link href="/privacy" target="_blank" rel="noopener noreferrer">
              Privacy <span className="sr-only">(opens in a new tab)</span>
              <span aria-hidden="true">↗</span>
            </Link>
          </nav>
          <a href="#workspace" className="header-cta">
            Let’s sync <ArrowUpRight size={15} />
          </a>
        </header>
        <main id="main-content">
          <Hero reducedMotion={preferences.reducedMotion} />
          <div className="workspace-intro" id="workspace">
            <div>
              <p className="eyebrow">
                <span className="status-dot" /> YOUR DAILY RESET
              </p>
              <h2>
                A little space for <em>clarity.</em>
              </h2>
            </div>
            <p>
              Bring the messy version.
              <br />
              Leave with the ready-to-share one.
            </p>
          </div>
          <div className="workbench-bar">
            <span>
              <span className="status-dot" /> THE WORKSPACE
            </span>
            <span>
              CAPTURE <span aria-hidden="true">/</span> ORGANIZE{" "}
              <span aria-hidden="true">/</span> REVIEW
            </span>
            <span className="workspace-session">
              PRIVATE SESSION <Icon name="shield" />
            </span>
          </div>
          <div className="workspace-body">
            <aside
              className="privacy-notice"
              aria-label="Processing and privacy"
            >
              <Icon name="shield" />
              <div>
                <p>
                  <strong>Your notes aren’t stored by Scrap2Sync.</strong>{" "}
                  {rulesMode
                    ? "External AI is disabled; this workspace uses conservative rules."
                    : "A configured external AI provider may process your notes."}{" "}
                  <Link
                    href="/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    How privacy works
                    <span className="sr-only"> (opens in a new tab)</span>
                  </Link>
                </p>
                <p>
                  Remove credentials and restricted information. Evaluated for
                  English notes; other languages are best effort.
                </p>
              </div>
            </aside>
            <div className="workspace-grid">
              <section
                className="workspace-panel source-panel"
                aria-labelledby="source-title"
              >
                <div className="panel-heading">
                  <div>
                    <p className="panel-kicker">
                      <span>01</span> THE INPUT
                    </p>
                    <h2 id="source-title">A place for the messy.</h2>
                  </div>
                  <FileText
                    className="panel-icon"
                    size={20}
                    aria-hidden="true"
                  />
                </div>
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    submit();
                  }}
                  onKeyDown={(event) => {
                    if (
                      (event.ctrlKey || event.metaKey) &&
                      event.key === "Enter"
                    ) {
                      event.preventDefault();
                      submit();
                    }
                  }}
                >
                  <div className="sample-row">
                    <span>Start with a thought. Or a few.</span>
                    <button
                      type="button"
                      className="text-button sample-button"
                      disabled={busy || !!notes.trim()}
                      onClick={() => {
                        setNotes(
                          "Yesterday: shipped the new onboarding flow\nYesterday: fixed the mobile navigation bug\nToday: connect the preferences API\nToday: review the dashboard designs\nBlockers: waiting on the final icon assets",
                        );
                        generation.clearValidationError();
                        document.getElementById("raw-notes")?.focus();
                      }}
                    >
                      <Plus size={13} /> Try an example
                    </button>
                  </div>
                  <NotesInput
                    value={notes}
                    onChange={(value) => {
                      setNotes(value);
                      setAnnouncement("");
                      generation.clearValidationError();
                    }}
                    disabled={busy}
                    errors={noteErrors}
                  />
                  <StyleProfileControl
                    profile={profile}
                    onChange={updateProfile}
                    disabled={busy}
                    errors={fields}
                  />
                  <div className="generate-row">
                    <button
                      ref={generateButton}
                      className="button primary generate-button"
                      type="submit"
                      disabled={
                        !normalizeNotes(notes) ||
                        !!localNotesError ||
                        !!Object.keys(profileErrors(profile)).length ||
                        busy ||
                        retrySeconds > 0
                      }
                    >
                      <Icon name="spark" />
                      {busy
                        ? "Organizing…"
                        : response
                          ? "Regenerate draft"
                          : "Generate draft"}
                      <Icon name="arrow" />
                    </button>
                    {busy && (
                      <button
                        className="button secondary"
                        type="button"
                        onClick={() => {
                          generation.cancel();
                          setAnnouncement("");
                        }}
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                  <p className="keyboard-hint">
                    <kbd>Ctrl</kbd> / <kbd>⌘</kbd> + <kbd>Enter</kbd> to
                    generate · Always review before copying
                  </p>
                </form>
              </section>
              <section
                className="workspace-panel result-panel"
                aria-labelledby="draft-title"
                data-generation-state={generation.state}
              >
                <div className="panel-heading">
                  <div>
                    <p className="panel-kicker">
                      <span>02</span> THE OUTPUT
                    </p>
                    <h2 id="draft-title">The clear version.</h2>
                  </div>
                  {draft && (
                    <button
                      className="button secondary copy-all-button"
                      type="button"
                      onClick={() => void copy()}
                      disabled={!!editError}
                    >
                      <Icon name="copy" />
                      Copy All
                    </button>
                  )}
                </div>
                <GenerationStatus
                  state={generation.state}
                  error={generation.error}
                  announcement={announcement}
                  retrySeconds={retrySeconds}
                />
                {draft && response ? (
                  <>
                    <div className="draft-meta">
                      <span
                        className={`mode-chip ${response.engineVersion === "rules-fallback-v1" ? "rules-chip" : ""}`}
                      >
                        {response.engineVersion === "rules-fallback-v1"
                          ? "Rules draft"
                          : "AI draft"}
                      </span>
                      {dirty && (
                        <span className="edited-label">
                          Unsaved edits · this page only
                        </span>
                      )}
                      {generation.clientDurationMs !== null && (
                        <span
                          className="latency-label"
                          data-client-duration-ms={generation.clientDurationMs}
                        >
                          Ready in{" "}
                          {(generation.clientDurationMs / 1000).toFixed(2)}s on
                          this request
                        </span>
                      )}
                    </div>
                    {globalWarnings.length > 0 && (
                      <aside
                        className="warning-region"
                        aria-label="Draft review warnings"
                      >
                        {globalWarnings.map((warning) => (
                          <div
                            key={warning.warningId}
                            className="warning-message"
                          >
                            <Icon name="warning" />
                            <p>
                              {warning.message}
                              {warning.sourceFragmentIds.length > 0 &&
                                !warning.itemId && (
                                  <span className="warning-context">
                                    {" "}
                                    Review the affected source notes alongside
                                    your draft.
                                  </span>
                                )}
                              {warning.itemId && (
                                <span className="warning-context">
                                  {" "}
                                  The original affected item has been removed
                                  from this draft.
                                </span>
                              )}
                            </p>
                          </div>
                        ))}
                      </aside>
                    )}
                    {editError && (
                      <p className="field-errors" role="status">
                        {editError}
                      </p>
                    )}
                    <StandupDraft
                      draft={draft}
                      profile={profile}
                      warnings={response.warnings}
                      busy={busy}
                      copyDisabled={!!editError}
                      onEdit={editItem}
                      onMove={moveItem}
                      onDelete={deleteItem}
                      onAdd={addItem}
                      onCopy={(section) => void copy(section)}
                    />
                  </>
                ) : (
                  <div className="draft-empty">
                    <div className="empty-illustration" aria-hidden="true">
                      <div className="paper-back" />
                      <div className="illustration-sheet">
                        <span className="paper-label">YOUR DAILY SYNC</span>
                        <span className="paper-rule" />
                        <div className="paper-group">
                          <i />
                          <span />
                          <span />
                        </div>
                        <div className="paper-group">
                          <i />
                          <span />
                          <span />
                        </div>
                        <div className="paper-group">
                          <i />
                          <span />
                        </div>
                        <span className="paper-check">
                          <Icon name="check" />
                        </span>
                      </div>
                      <span className="illustration-spark">✳</span>
                    </div>
                    <h3>Clarity is on the other side.</h3>
                    <p>
                      Your notes, organized. Your voice, intact.
                      <br />
                      Add your thoughts and generate your first draft.
                    </p>
                    <div className="empty-labels">
                      <span>Yesterday</span>
                      <span>Today</span>
                      <span>Blockers</span>
                    </div>
                  </div>
                )}
                {manualCopy !== null && (
                  <div className="manual-copy">
                    <label htmlFor="manual-copy">
                      Plain-text copy fallback
                    </label>
                    <p>
                      Clipboard access was unavailable. Copy the selected text
                      with Ctrl+C or ⌘C.
                    </p>
                    <textarea
                      id="manual-copy"
                      ref={manualCopyField}
                      value={manualCopy}
                      readOnly
                      rows={10}
                    />
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => setManualCopy(null)}
                    >
                      Close manual copy
                    </button>
                  </div>
                )}
              </section>
            </div>
          </div>
          <section
            className="workspace-footer"
            aria-label="Workspace preferences"
          >
            <div>
              <p className="footer-promise">
                Your work. Your words. A little more organized.
              </p>
              <p>Notes and drafts clear when you reload or leave this page.</p>
            </div>
            <div className="preference-actions">
              <label className="motion-control">
                <input
                  type="checkbox"
                  checked={preferences.reducedMotion}
                  onChange={(event) =>
                    savePreferences({
                      ...preferences,
                      reducedMotion: event.target.checked,
                    })
                  }
                />
                Reduce visual motion
              </label>
              <button
                className="text-button"
                type="button"
                onClick={() => {
                  resetPreferences();
                  setProfileOverride(null);
                  setAnnouncement(
                    "Preferences reset. Your notes and draft are unchanged.",
                  );
                }}
              >
                Reset preferences
              </button>
            </div>
          </section>
          <Process />
        </main>
        <footer className="site-footer">
          <div className="footer-top">
            <span>GOOD WORK DESERVES CLEAR WORDS.</span>
            <a href="#workspace">
              Make your next update count <ArrowUpRight size={16} />
            </a>
          </div>
          <div className="footer-wordmark" aria-hidden="true">
            Scrap<span>2</span>Sync<span className="wordmark-period">.</span>
          </div>
          <div className="footer-bottom">
            <span>© {new Date().getFullYear()} Scrap2Sync</span>
            <span>A little more clarity. A little less noise.</span>
            <a href="#main-content">
              BACK TO TOP <ArrowDown size={12} />
            </a>
          </div>
        </footer>
        <Dialog.Root open={confirmReplace} onOpenChange={setConfirmReplace}>
          <Dialog.Portal>
            <div className="dialog-backdrop" aria-hidden="true" />
            <Dialog.Content
              className="dialog-content"
              onCloseAutoFocus={(event) => {
                event.preventDefault();
                generateButton.current?.focus();
              }}
            >
              <div className="dialog-symbol">
                <Icon name="warning" />
              </div>
              <Dialog.Title>Replace your edited draft?</Dialog.Title>
              <Dialog.Description>
                You’ve changed this draft. Generating again will replace those
                edits with a new draft from your notes.
              </Dialog.Description>
              <div className="dialog-actions">
                <Dialog.Close asChild>
                  <button className="button secondary">Keep my edits</button>
                </Dialog.Close>
                <button
                  className="button primary"
                  onClick={() => {
                    setConfirmReplace(false);
                    void generation.generate(notes, profile);
                  }}
                >
                  Replace and generate
                </button>
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </div>
    </Experience>
  );
}
