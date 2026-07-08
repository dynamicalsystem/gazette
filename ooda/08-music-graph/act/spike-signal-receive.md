# Act: spike -- muster over gazette's Signal receive path

Run 2026-07-08. First Act of loop 08. Outcome: **success** -- publishing a muster and
folding Signal reactions into a live roster+ledger works end to end. Spike code:
`spikes/muster_receive_spike.py` (branch `feat/08-signal-muster-spike`).

## What was tested

Sent a marked test muster to the Abyss group via `/v2/send`, reacted on a phone, and
read reactions back to build a roster. Ran against the live gigbot signal-cli over
WireGuard.

## Findings

1. **Correlation is exact and free.** A reaction envelope carries
   `dataMessage.reaction.targetSentTimestamp`, which equals the `timestamp` returned by
   `/v2/send` when the muster was posted. So a reaction maps to *its* muster with zero
   ambiguity -- the sent timestamp IS the muster id.
2. **Sender is identified**: `envelope.sourceName` / `sourceNumber` / `sourceUuid`.
3. **Join / leave / paid**: `reaction.emoji` + `reaction.isRemove`. Spike convention:
   any emoji = join (`in`), a money emoji (£/$/💷/💰/💵/✅) = `paid`, `isRemove` = leave.
   Observed fold: `{} -> {Simon: in} -> {Simon: paid}` and remove -> drop.
4. **Group context is free**: `dataMessage.groupInfo` (`groupId`, `groupName`).
5. **Replies/quotes** carry `dataMessage.quote` (with the target's timestamp) + text --
   a second, richer input channel beyond reactions (not exercised deeply here).

## The load-bearing constraint (the real learning)

signal-cli runs in **json-rpc mode**, so:
- `/v1/receive` is **websocket-only** -- `ws://.../v1/receive/{number}`. HTTP GET returns
  `400 "not using the websocket protocol"`.
- **Messages are dropped when no websocket client is attached.** They are NOT buffered
  for a later poll. Reactions made while disconnected are lost.

=> The muster service must hold a **persistent websocket listener** to signal-cli, not a
poll. This is a natural fit for the long-running `gazette serve` (loop 06): serve owns
the listener, folds reactions into muster state.

## Side finding (fix later)

`publishers.py::_drain_inbox` does an HTTP GET on `/v1/receive` -- a **no-op in json-rpc
mode** (400). The Signal drain-and-retry path therefore never actually drains. The
transient-retry hardening (v0.1.6) still works because it retries regardless, but the
drain branch is dead. Fix: drain via the ws, or drop the branch.

## Shape of the muster build (implied)

- **publish**: `/v2/send` returns the muster id (timestamp). Already works.
- **store**: `{ muster_id -> muster record }` (roster, ledger, state, anchor, locus, moment).
- **listen**: a persistent ws listener in `gazette serve` folds
  reactions/replies -> roster + ledger + state transitions, keyed by `targetSentTimestamp`.
- **remind**: scheduled re-publish of the current snapshot (gazette scheduler pattern).
- No PDS / ZK / atproto required for this slice -- it runs on shipped gazette machinery
  plus a ws listener and a state model.

## Open questions surfaced

- Reaction semantics: which emoji means what, and who may set `paid` (self-serve vs
  organiser-confirms)? The spike let anyone self-mark; real musters may want organiser
  confirmation for money.
- One ws listener for one identity (gigbot) multiplexes ALL groups' reactions -> the
  listener must route by `groupInfo.groupId` + `targetSentTimestamp` to the right muster.
- Reply/quote parsing (free-text commands: "+1", "can't make it", "paid £12") is a
  richer but fuzzier input channel than reactions.

## Cross-references
- `../orient/coordination-primitive.md` -- the muster this drives (service=truth,
  chat=comms adapter); this spike is the "ingest-in" seam it named.
- `spikes/muster_receive_spike.py` -- the spike (send / raw / watch).
- `gazette/src/dynamicalsystem/gazette/publishers.py` -- `/v2/send` contract + the dead
  `_drain_inbox` to fix.
