# Security policy

## Supported version

Security fixes are applied to the latest revision of `main`. Older commits,
forks, and unmaintained deployments are not supported release channels.

## Reporting a vulnerability

Please use GitHub's **Report a vulnerability** form in the repository Security
tab so details remain private. Include the affected revision, impact, minimal
reproduction steps, and any suggested mitigation. Do not include real user notes,
credentials, secrets, or private provider data.

If private vulnerability reporting is unavailable, open a minimal public issue
asking the maintainer to establish a private contact channel. Do not disclose the
vulnerability, exploit details, or secrets in that issue.

Please allow the maintainer time to reproduce and remediate a report before
public disclosure. Coordinated credit can be arranged with the reporter.

## Security boundaries

Scrap2Sync does not promise safe handling of secrets entered as notes. Operators
must keep the formatter disabled or complete the provider review described in
`docs/PRIVACY.md` and `docs/DEPLOYMENT.md`. Production deployments must preserve
the documented HTTPS, exact-origin, proxy, rate, concurrency, CSP, non-root
container, secret-manager, and log-redaction controls.
