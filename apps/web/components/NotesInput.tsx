"use client";

import { useLayoutEffect, useRef } from "react";
import { codePointLength, MAX_NOTES, normalizeNotes } from "@/lib/profiles";

export function NotesInput({
  value,
  onChange,
  disabled,
  errors,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
  errors: string[];
}) {
  const input = useRef<HTMLTextAreaElement>(null);
  useLayoutEffect(() => {
    if (input.current) {
      input.current.style.height = "auto";
      input.current.style.height = `${Math.max(245, input.current.scrollHeight)}px`;
    }
  }, [value]);
  const length = codePointLength(normalizeNotes(value));
  return (
    <div className="notes-field">
      <div className="field-heading">
        <label htmlFor="raw-notes">Rough notes</label>
        <span
          className={`character-count ${length > MAX_NOTES ? "text-danger" : ""}`}
          id="notes-count"
        >
          {length.toLocaleString("en-US")} / 10,000
        </span>
      </div>
      <textarea
        ref={input}
        id="raw-notes"
        name="rawNotes"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        readOnly={disabled}
        aria-invalid={errors.length > 0}
        aria-describedby={`notes-hint notes-count${errors.length ? " notes-errors" : ""}`}
        placeholder={
          "Yesterday: finished the settings screen\nToday: connect the preferences API\nBlocked: waiting on the final icon assets"
        }
        spellCheck={false}
      />
      <p className="field-hint" id="notes-hint">
        Messy is fine. Add what happened, what’s next, and anything in the way.
      </p>
      {errors.length > 0 && (
        <ul className="field-errors" id="notes-errors">
          {errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
