# Gazette production publishing runbook

This runbook covers how to run gazette against production targets safely. The
default is always dry-run; live publishers require two explicit choices.

## Default behaviour

```bash
gazette publish
```

Runs every configured watermark through the `Validator` publisher. It logs what
would be published but does not post to Signal, Bluesky, or any other live
target. This is the safe way to validate the current state.

## Live prod publishing

Live publishers are enabled only when **both** of these are true:

1. The `--live` flag is passed to `gazette publish`.
2. The environment variable `GAZETTE_LIVE=1` is set.

Example:

```bash
GAZETTE_LIVE=1 gazette publish --live
```

If `--live` is passed without `GAZETTE_LIVE=1`, the command exits immediately
with an error and no target is touched.

The scheduled Quadlet timer unit (`gazette-publish.timer`) is the only routine
process that should run with live publishers. It must be updated to pass both
`--live` and `GAZETTE_LIVE=1`; see the coordination note below.

## When is live prod access permitted?

Live prod access is permitted only when all of these are true:

- You are responding to a confirmed production fault or performing a planned
  deploy that has been reviewed.
- You have already validated the change with `gazette publish` (dry-run).
- You understand which watermarks will advance and which targets will be posted
  to.
- You have a way to recover the watermark state if something goes wrong (see
  below).

Never use prod as a test environment. If a fix cannot be validated offline,
use a non-prod target or obtain explicit human approval before posting live.

## Advancing or resetting a watermark

To move a watermark forward by one placing (e.g., to restore Abyss's one-day
lead):

```bash
podman exec -ti gazette python - <<'PY'
from dynamicalsystem.gazette.watermarks import Watermark
w = Watermark('abyss')
print(f"before: {w.chart}.{w.placing}")
w.update()
w._load()
print(f"after:  {w.chart}.{w.placing}")
PY
```

Before doing this:

1. Check the current watermark: `cat $DATA_FOLDER/watermarks.json`.
2. Confirm the chart and target are what you expect.
3. Verify the review at the new placing exists and is valid with `gazette publish`
   (dry-run).

After doing this:

1. Check that `watermarks.log` contains the expected entry.
2. Run `gazette publish` (dry-run) to confirm the next scheduled run will do
   what you expect.

## Restoring watermark state from backup

Every `Watermark.update()` writes a backup to `watermarks.json.bak` before
modifying `watermarks.json`. To roll back:

```bash
DATA_DIR="/path/to/data/folder"
cp "$DATA_DIR/watermarks.json.bak" "$DATA_DIR/watermarks.json"
```

Then verify the restored state:

```bash
cat "$DATA_DIR/watermarks.json"
```

## Coordination: updating the Quadlet unit

The gazette container image changed its CLI default to dry-run. The tinsnip
Quadlet unit that runs the scheduled publish must be updated to pass `--live`
and set `GAZETTE_LIVE=1` before the new image is deployed to production. Until
that update is in place, the scheduled timer will run dry and no live content
will be published.

Add to `gazette-publish.container` (or equivalent):

```ini
[Container]
Exec=gazette publish --live
Environment=GAZETTE_LIVE=1
```

Do not set `GAZETTE_LIVE=1` in the global `EnvironmentFile=`; keep it scoped to
this unit's `Exec` line.
