# Container verification status

Remote base-image vulnerability scans ran without a container engine. They are
saved as `reports/python-base-image.json` and `reports/python-alpine-base.json`.
These reports describe their respective unmodified base images, not the final
application image. The original Debian Bookworm base was rejected after its scan
reported 62 high/critical package findings.

The Dockerfile now uses the official Python 3.14.7 Alpine 3.24 image, pinned to
`sha256:c6ead215bfd31f1e433d968853b7a769989117115b728874824e6c0a27cb96fc`.
Its unmodified scan identified seven util-linux/libuuid findings and vulnerable
global msgpack/setuptools installations. The runtime stage installs exact
`libuuid=2.42.3-r1`, which addresses all seven reported libuuid findings, and removes
the unused global packaging tools and msgpack. The application has no dependency
on these global Python packages; uv creates its separate locked environment.

Package availability/version was verified on 2026-09-12 against the official
[Alpine 3.24 x86_64 index](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/x86_64/APKINDEX.tar.gz).
The immutable image manifest was resolved from the official Docker library
registry. The Python runtime version is unchanged. Both development locks and
the image's package version remain explicit.

**Remediation is configured, not runtime-verified.** This Windows host has no
Docker/Podman engine or functioning WSL installation. The Linux container build,
musllinux dependency installation, non-root runtime smoke and final image scan
must pass in CI or on a container-capable host. No finding is suppressed, no
exception is self-approved, and the CI high/critical failure threshold remains
enabled. Until those checks run successfully, do not claim the final image is
verified or production-ready.
