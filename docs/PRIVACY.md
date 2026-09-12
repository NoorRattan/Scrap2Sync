# Privacy

Scrap2Sync organizes notes in memory. It has no account, database, server history,
product analytics or tracking identifiers. Notes, drafts and warnings stay in
the current browser page and API request lifetime. Closing or reloading the page
loses this content. Remove credentials and highly restricted information before
submitting notes.

The browser may save a structured style preference and visual preference under a
versioned key. Reset preferences removes it. Notes, drafts, warnings, request IDs,
timestamps and usage history are never preference data. Blocked storage does not
prevent generation or copying. Clipboard access occurs only when you choose Copy.

## External processing

The default installation has its provider disabled. Its deterministic formatter
processes notes on the local API and makes no AI provider request.

The optional integration supports OpenAI's Responses API. It sends the minimum
source fragments and selected structured style over HTTPS, requests strict
structured output, enables no tools and sets `store: false`. It never uses an
external URL supplied in notes as a request destination.

Operator-selected model: **not configured**. Processing region: **not verified**.
Account-specific retention, zero-data-retention eligibility, regional processing,
pricing and quotas: **not verified**. The primary formatter stays disabled until
an operator verifies these details and explicitly enables it. Local fallback does
not establish the privacy properties of an external provider.

OpenAI's [data controls documentation](https://developers.openai.com/api/docs/guides/your-data)
was checked on 2026-09-05. API data is not used for training by default unless an
organization opts in. `store: false` avoids Responses application-state storage;
it does not by itself promise zero retention of abuse-monitoring logs. Account
and regional controls must be verified against current provider documentation.

## Logs, caching and cancellation

Application logs contain only bounded operational fields such as a server request
ID, status category, formatter family and duration. They exclude notes, drafts,
labels, provider bodies, credentials, client IDs and full client IP addresses.
The API uses `Cache-Control: no-store`. Local application logs go to the terminal;
Scrap2Sync does not create a log file. If an operator captures stdout, retain it
for at most 24 hours locally and restrict access. Production retention and access
ownership are explicit deployment decisions.

Cancel aborts the browser request and discards late results. Cancellation may not
stop a request already received by an external provider. Notes are never saved to
resume a cancelled operation, and retries require a new user submission.

## Before enabling a provider

Record the exact model, region, retention/training settings, verification date,
responsible operator and limitations. Update the public privacy page to match.
Verify the provider budget, quota alerts and emergency disable switch. A config
flag records this decision; it is not proof that the checks have been performed.
