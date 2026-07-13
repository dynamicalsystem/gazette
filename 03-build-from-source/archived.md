loop: 03-build-from-source
closed: 2026-06-26
outcome: met -- `podman build .` ships the working tree; no PyPI in the deploy path

Key result: dockerfile installs from ./gazette (hatchling), base python:3.13-slim,
/data volume, ENTRYPOINT ["gazette"]; makefile image target decoupled from publish.
Outcomes O1-O4 met (see README).
Note: multi-stage slimming deferred; missing-watermark crash left to a bug pass.
Successors: 05 (CI->GHCR), 06 (dockerfile CMD=serve).
