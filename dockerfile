# syntax=docker/dockerfile:1
#
# Build gazette from local source -- no PyPI publish in the deploy path.
#   podman build -t dynamicalsystem/gazette .
#
# Debian slim (not alpine): manylinux wheels exist for pydantic-core/atproto,
# so the build needs no compiler toolchain.
FROM python:3.13-slim

WORKDIR /app

# Install the gazette package from the working tree. hatchling builds it in an
# isolated, discarded build env, so no build tooling lingers in the image.
COPY gazette/ ./gazette/
RUN pip install --no-cache-dir ./gazette

# Watermark state lives on a mounted volume; config arrives via env (.env / Vault).
ENV DATA_FOLDER=/data \
    WATERMARK_FILE=watermarks.json
RUN mkdir -p /data
VOLUME ["/data"]

# Long-lived web service by default (`gazette serve`); the one-shot publish sweep
# is `podman run <img> publish`. Timing is systemd's job (loop 07), not the image.
EXPOSE 8000
ENTRYPOINT ["gazette"]
CMD ["serve"]
