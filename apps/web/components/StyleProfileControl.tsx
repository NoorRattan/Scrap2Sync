"use client";

import { BUILTIN_PROFILES, CUSTOM_PROFILE } from "@/lib/profiles";
import { SECTIONS, type StyleProfile } from "@/lib/types";

const descriptions = [
  "Short & direct",
  "A little more context",
  "Room for the details",
  "Make it your format",
];

export function StyleProfileControl({
  profile,
  onChange,
  disabled,
  errors,
}: {
  profile: StyleProfile;
  onChange: (profile: StyleProfile) => void;
  disabled: boolean;
  errors: Record<string, string[]>;
}) {
  function errorProps(field: string) {
    return {
      "aria-invalid": !!errors[field]?.length,
      "aria-describedby": errors[field]?.length ? `${field}-error` : undefined,
    };
  }
  function errorText(field: string) {
    return errors[field]?.length ? (
      <p className="field-errors" id={`${field}-error`}>
        {errors[field].join(" ")}
      </p>
    ) : null;
  }
  return (
    <fieldset className="style-fieldset" disabled={disabled}>
      <legend>Style profile</legend>
      <div className="profile-grid">
        {[...BUILTIN_PROFILES, CUSTOM_PROFILE].map((item, index) => (
          <label
            key={item.id}
            className={`profile-option ${profile.id === item.id ? "selected" : ""}`}
          >
            <input
              type="radio"
              name="style-profile"
              value={item.id}
              checked={profile.id === item.id}
              onChange={() => onChange(item)}
            />
            <span className="profile-name">
              {item.label}
              <span className="radio-indicator" aria-hidden="true" />
            </span>
            <span className="profile-description">{descriptions[index]}</span>
          </label>
        ))}
      </div>
      {profile.id === "custom" && (
        <div className="custom-profile">
          <div className="custom-field">
            <label htmlFor="profile-label">Profile name</label>
            <input
              id="profile-label"
              value={profile.label}
              onChange={(event) =>
                onChange({ ...profile, label: event.target.value })
              }
              {...errorProps("styleProfile.label")}
            />
            {errorText("styleProfile.label")}
          </div>
          <div className="custom-grid">
            <div className="custom-field">
              <label htmlFor="profile-layout">Layout</label>
              <select
                id="profile-layout"
                value={profile.layout}
                onChange={(event) =>
                  onChange({
                    ...profile,
                    layout: event.target.value as StyleProfile["layout"],
                  })
                }
              >
                <option value="bullets">Bullets</option>
                <option value="paragraphs">Paragraphs</option>
              </select>
            </div>
            <div className="custom-field">
              <label htmlFor="profile-verbosity">Detail</label>
              <select
                id="profile-verbosity"
                value={profile.verbosity}
                onChange={(event) =>
                  onChange({
                    ...profile,
                    verbosity: event.target.value as StyleProfile["verbosity"],
                  })
                }
              >
                <option value="brief">Brief</option>
                <option value="standard">Standard</option>
              </select>
            </div>
            <div className="custom-field">
              <label htmlFor="profile-tone">Tone</label>
              <select
                id="profile-tone"
                value={profile.tone}
                onChange={(event) =>
                  onChange({
                    ...profile,
                    tone: event.target.value as StyleProfile["tone"],
                  })
                }
              >
                <option value="direct">Direct</option>
                <option value="neutral-professional">
                  Neutral professional
                </option>
              </select>
            </div>
            <div className="custom-field">
              <label htmlFor="profile-items">Preferred items per section</label>
              <select
                id="profile-items"
                value={profile.preferredMaxItemsPerSection}
                onChange={(event) =>
                  onChange({
                    ...profile,
                    preferredMaxItemsPerSection: Number(event.target.value),
                  })
                }
              >
                {Array.from({ length: 10 }, (_, index) => (
                  <option key={index + 1}>{index + 1}</option>
                ))}
              </select>
            </div>
          </div>
          {SECTIONS.map((section) => (
            <div className="custom-field" key={section}>
              <label htmlFor={`header-${section}`}>
                {section === "yesterday"
                  ? "Yesterday"
                  : section === "today"
                    ? "Today"
                    : "Blockers"}{" "}
                heading
              </label>
              <input
                id={`header-${section}`}
                value={profile.headers[section]}
                onChange={(event) =>
                  onChange({
                    ...profile,
                    headers: {
                      ...profile.headers,
                      [section]: event.target.value,
                    },
                  })
                }
                {...errorProps(`styleProfile.headers.${section}`)}
              />
              {errorText(`styleProfile.headers.${section}`)}
            </div>
          ))}
          <p className="field-hint">
            Item counts guide presentation. Keeping your facts takes priority.
          </p>
        </div>
      )}
    </fieldset>
  );
}
