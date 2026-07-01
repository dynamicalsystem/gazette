# Loop 05: CI to GHCR + drop legacy deploy

Make gazette's CI build a multi-arch image and push it to GHCR on merge to main,
matching the tinsnip fleet model, and delete the legacy homelab deploy artifacts.

## Why

The target deploy is the tinsnip quadlet model: each service's own CI builds and
pushes `ghcr.io/<owner>/<svc>:latest` (multi-arch; arm64 for the Ampere box) and
`podman auto-update` pulls it. gazette's existing `.github/workflows/build-and-push.yml`
predates all of this:

- pushes to Docker Hub, not GHCR;
- still sets halogen-era env names (`CONTENT_*`/`PUBLISHERS_*`/`WATERMARKS_*`) that
  loop 01 deleted;
- publishes to PyPI and passes `NAMESPACE`/`SCRIPT` build-args the loop-03 dockerfile
  no longer accepts;
- gates on a test suite that is knowingly red (live-service integration tests).

The `docker-compose.yml` (old homelab, `kalmanfilter` net, from the tangled.sh tinsnip)
and the `deploy.sh` curl-pipe-bash installer are the old deploy path we are abandoning.

## Scope

In:
- New `.github/workflows/release.yml` mirroring festers: log in to GHCR with the
  workflow `GITHUB_TOKEN`, QEMU + Buildx, build `linux/amd64,linux/arm64` from
  `./dockerfile`, push `ghcr.io/dynamicalsystem/gazette` tagged `latest` (default
  branch) + `sha` + semver. No Docker Hub, no PyPI, no build-args.
- Delete the stale `.github/workflows/build-and-push.yml`.
- Delete `docker-compose.yml` and `deploy.sh`.
- Rewrite the top-level `README.md` Deploy section: image comes from GHCR, the box
  runs it as a tinsnip quadlet (loop 07). No curl-pipe-bash, no compose.

Out:
- A gating test CI (`ci.yml`) -- deferred to the test-suite repair loop; the suite
  is red today and would block merges.
- The service pivot (loop 06) and the quadlet itself (loop 07).

## Outcomes and tests

### O1: merge to main publishes a multi-arch GHCR image
- T1.1: `release.yml` on push-to-main builds `linux/amd64,linux/arm64` and pushes
  `ghcr.io/dynamicalsystem/gazette:latest`. Verified by a green Actions run + the
  package appearing under GHCR with both arches.

### O2: no Docker Hub / PyPI / halogen residue in CI
- T2.1: `grep -riE "docker.io|dockerhub|PYPI|CONTENT_|PUBLISHERS_|WATERMARKS_|build-args"
  .github` returns nothing.

### O3: legacy deploy artifacts gone
- T3.1: `docker-compose.yml`, `deploy.sh` absent; `README.md` no longer references
  them or `curl | bash`.

### O4: main is on origin
- T4.1: local main (incl. the merged legacy commits and this loop) pushed; working
  tree clean; `origin/main == main`.
