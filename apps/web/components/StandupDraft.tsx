"use client";

import { useLayoutEffect, useRef } from "react";
import { sectionPlaceholder } from "@/lib/copyFormat";
import {
  SECTIONS,
  type GenerationWarning,
  type LocalDraft,
  type LocalItem,
  type Section,
  type StyleProfile,
} from "@/lib/types";
import { Icon } from "./ui/Icon";

function ItemEditor({
  item,
  section,
  index,
  profile,
  warnings,
  busy,
  onEdit,
  onMove,
  onDelete,
}: {
  item: LocalItem;
  section: Section;
  index: number;
  profile: StyleProfile;
  warnings: GenerationWarning[];
  busy: boolean;
  onEdit: (id: string, text: string) => void;
  onMove: (id: string, target: Section) => void;
  onDelete: (id: string) => void;
}) {
  const input = useRef<HTMLTextAreaElement>(null);
  useLayoutEffect(() => {
    if (input.current) {
      input.current.style.height = "auto";
      input.current.style.height = `${Math.max(58, input.current.scrollHeight)}px`;
    }
  }, [item.text]);
  return (
    <div
      className={`draft-item ${item.userEdited ? "user-edited" : ""}`}
      data-item-id={item.itemId}
    >
      <div className="item-topline">
        <label htmlFor={`item-${item.itemId}`}>
          {profile.headers[section]} item {index + 1}
        </label>
        {item.userEdited && <span className="edited-label">Edited by you</span>}
      </div>
      <textarea
        ref={input}
        id={`item-${item.itemId}`}
        value={item.text}
        onChange={(event) => onEdit(item.itemId, event.target.value)}
        readOnly={busy}
        aria-describedby={
          warnings.length ? `warnings-${item.itemId}` : undefined
        }
        rows={2}
        spellCheck={false}
      />
      {warnings.length > 0 && (
        <ul className="item-warnings" id={`warnings-${item.itemId}`}>
          {warnings.map((warning) => (
            <li key={warning.warningId}>
              <Icon name="warning" />
              <span>{warning.message}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="item-actions">
        <label className="move-control">
          <span>Move to</span>
          <select
            aria-label={`Move ${profile.headers[section]} item ${index + 1} to`}
            value={section}
            onChange={(event) =>
              onMove(item.itemId, event.target.value as Section)
            }
            disabled={busy}
          >
            {SECTIONS.map((target) => (
              <option key={target} value={target}>
                {profile.headers[target]}
              </option>
            ))}
          </select>
        </label>
        <button
          className="text-button delete-button"
          type="button"
          onClick={() => onDelete(item.itemId)}
          disabled={busy}
          aria-label={`Delete ${profile.headers[section]} item ${index + 1}`}
        >
          <Icon name="close" />
          Delete
        </button>
      </div>
    </div>
  );
}

export function StandupDraft({
  draft,
  profile,
  warnings,
  busy,
  copyDisabled,
  onEdit,
  onMove,
  onDelete,
  onAdd,
  onCopy,
}: {
  draft: LocalDraft;
  profile: StyleProfile;
  warnings: GenerationWarning[];
  busy: boolean;
  copyDisabled: boolean;
  onEdit: (id: string, text: string) => void;
  onMove: (id: string, target: Section) => void;
  onDelete: (id: string) => void;
  onAdd: (section: Section) => void;
  onCopy: (section: Section) => void;
}) {
  return (
    <div className="draft-sections">
      {SECTIONS.map((section, index) => (
        <section
          className={`draft-section section-${section}`}
          key={section}
          aria-labelledby={`section-${section}`}
        >
          <div className="section-heading">
            <div className="section-title">
              <span className="section-marker" aria-hidden="true">
                0{index + 1}
              </span>
              <h3 id={`section-${section}`}>{profile.headers[section]}</h3>
              <span
                className="item-count"
                aria-label={`${draft[section].length} items`}
              >
                {draft[section].length}
              </span>
            </div>
            <button
              className="text-button"
              onClick={() => onCopy(section)}
              disabled={copyDisabled}
              aria-label={`Copy ${profile.headers[section]} section`}
            >
              <Icon name="copy" />
              Copy section
            </button>
          </div>
          {draft[section].length ? (
            draft[section].map((item, itemIndex) => (
              <ItemEditor
                key={item.itemId}
                item={item}
                section={section}
                index={itemIndex}
                profile={profile}
                warnings={warnings.filter(
                  (warning) => warning.itemId === item.itemId,
                )}
                busy={busy}
                onEdit={onEdit}
                onMove={onMove}
                onDelete={onDelete}
              />
            ))
          ) : (
            <p className="empty-section">{sectionPlaceholder(section)}</p>
          )}
          <button
            className="text-button add-button"
            type="button"
            onClick={() => onAdd(section)}
            disabled={busy}
            aria-label={`Add item to ${profile.headers[section]}`}
          >
            <Icon name="plus" />
            Add item
          </button>
        </section>
      ))}
    </div>
  );
}
