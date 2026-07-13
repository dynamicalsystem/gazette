# [ARCHIVED] Loop 03: build from local source

Make `podman build .` produce a runnable gazette image from the working tree,
with no PyPI publish anywhere in the build/deploy path.

## Why

The old build was a round trip through PyPI: `make image` depended on
`make publish` (twine upload), and the dockerfile did
`pip install dynamicalsystem.gazette` -- pulling the *published* package back
down. So every deploy required a release, and the container never ran local
source. That couples iteration speed to PyPI and makes "deploy this branch"
impossible without cutting a version.

## Scope

In:
- Rewrite `dockerfile` to install the package from `./gazette` (hatchling builds
  the wheel in an isolated, discarded build env). No build-args, no PyPI pull.
- Switch base from alpine to `python:3.13-slim` so pydantic-core/atproto install
  from manylinux wheels with no compiler in the image.
- `/data` volume for watermark state; `DATA_FOLDER`/`WATERMARK_FILE` defaults set
  as env. Config otherwise arrives via env (.env / Vault).
- `ENTRYPOINT ["gazette"]` (the `dynamicalsystem.gazette:main` console script).
- Rewrite `makefile`: `image` builds from source with no `publish` dependency;
  `build`/`check`/`publish` remain as an optional, separate PyPI path. `ENGINE`
  defaults to `podman`. Removed the dead `sync` target and stale build-args.

Out:
- docker-compose / scheduler / volumes-on-VPS (loop 04). The compose file still
  describes the old signal-in-repo + NFS layout and is rewritten there.

## Outcomes and tests

### O1: the image builds from the working tree, no PyPI publish
- T1.1: `podman build . -t dynamicalsystem/gazette` succeeds; log shows it
  *building* `dynamicalsystem.gazette` locally, not downloading it. [verified]

### O2: the image runs the app and is halogen-free
- T2.1: `gazette` console script on PATH; `import dynamicalsystem.gazette` ok. [verified]
- T2.2: `dynamicalsystem.halogen` ABSENT in the image. [verified]

### O3: run-to-completion against mounted state, no live services
- T3.1: `podman run -v <data>:/data dynamicalsystem/gazette` with an empty
  `watermarks.json` exits 0. [verified]

### O4: no test regression
- T4.1: suite 10 failed / 13 passed (unchanged; loop 03 touches only
  dockerfile/makefile). [verified]

## Notes

- Image is ~199 MB (slim). A multi-stage build (build wheel, copy into a clean
  runtime) would shrink it; deferred as a non-blocking optimization.
- Latent bug confirmed via the container: a *missing* watermark file makes
  `main()` iterate `None` and crash (an empty `{}` file is fine). Graceful
  handling belongs with the other pre-existing bugs (loop 05 / a bug-fix pass).

## Result (2026-06-26)

Done and verified. `make image` (or `podman build .`) ships the working tree;
PyPI is now an independent, optional release path.
