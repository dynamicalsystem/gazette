# dynamicalsystem.gazette

This is the uv workspace for [dynamicalsystem.gazette](https://github.com/DynamicalSystem/gazette/blob/main/gazette/README.md).

## Build

Build a runnable image from the local working tree (no PyPI round-trip):

```bash
make image        # podman build . --tag dynamicalsystem/gazette
```

## Deploy

Deployment is declarative, not a script. On merge to `main`, CI
(`.github/workflows/release.yml`) builds a multi-arch image (amd64 + arm64) and
pushes it to `ghcr.io/dynamicalsystem/gazette:latest`.

The `gateway` box runs that image as a rootless podman **Quadlet** systemd unit,
defined in the private `tinsnip` repo (`hosts/gateway/gazette.container`) and
pulled by `podman auto-update`. Config is an on-box `EnvironmentFile`; watermark
state is a mounted volume. See tinsnip for the box-side wiring.

Dry-runs (`gazette publish` without `--live`) use the `Validator` publisher,
never touch the prod Signal identity, and never change the watermark state --
see `docs/runbooks/prod-publishing.md` for the run model.
