---
loop: abyss-lead-invariant
product: gazette
owner: dynamicalsystem
status: Orient
parent: null
blocked-by: []
worktrees: []
prs: []
triggers: []
---

# Abyss lead invariant

## Status

Orient

**Owner:** dynamicalsystem

## Context

Abyss is the preview target: it must always publish a placing one sweep before
every prod target so a bad review is seen there first. Simon fell behind on
reviews this week and the Abyss watermark stopped moving. The suspicion is that
the prod targets (e.g. Josh) have drawn level with Abyss, and that nothing in
gazette stops that from happening. Raised 2026-09-12.

Two asks came with the signal:

1. Restore the Abyss lead now if the chart has enough written reviews.
2. Design a fix so prod targets can never draw level with Abyss again, without
   hardcoding target names into the code.

## Observations

Facts gathered 2026-09-12 from the `main` checkout, the content repo, and the
tinsnip quadlets. Prod watermark state is still unread (see the open item).

### Sweep mechanics (code)

- `publish_once` iterates every watermark in `watermarks.json` independently.
  For each one it publishes the current placing if the review classifies `ok`,
  then decrements the placing. There is no ordering, no cross-target rule, and
  no notion of a leader. (`gazette/src/dynamicalsystem/gazette/__init__.py`)
- Placings count DOWN. "One ahead" therefore means Abyss has the LOWER placing;
  prod targets sit at Abyss + 1, not Abyss - 1.
- `ReviewNotReady` (review not written yet) holds that one target quietly. The
  other targets in the same sweep carry on. This is the mechanism that lets
  followers catch up: Abyss holds on an unwritten placing while prod posts the
  placing Abyss published the day before.
- The publish-once guard is per target and only prevents re-posting the same
  placing within its window. It does nothing about relative position.
- The runbook (`docs/runbooks/prod-publishing.md`) documents "restore Abyss's
  one-day lead" as a manual `Watermark.update()` call. The lead is a human
  convention, not an enforced invariant.
- `watermarks.json` is a flat dict of routes: publisher, chart, placing,
  target. Nothing in it relates one route to another.

### Timer

- `gazette-publish.timer` fires daily at 07:00 Europe/London, `Persistent=true`.
- Data folder on the gateway: `/home/ubuntu/.local/state/dynamicalsystem/gazette`
  (mounted as `/data` in the container).

### Chart tQ26.H (content repo, fetched 2026-09-12)

| Metric | Value |
|---|---|
| Items | 100 |
| Reviews classified `ok` | placings 100 down to 31 (70) |
| Reviews `not_ready` | placings 30 down to 1 |
| Reviews `invalid` | none |

Recent commits touching the chart (UTC, message is the placing written):

| Date | Placing |
|---|---|
| 2026-09-05 17:03 | 37 |
| 2026-09-07 16:53 | 36 |
| 2026-09-09 08:00 | 35 |
| 2026-09-12 08:05 | 32 |
| 2026-09-12 09:13 | 33 |
| 2026-09-12 11:25 to 11:35 | 31 (three commits) |

Placing 34 does not appear as its own commit but classifies `ok`.

Reviews 36 and 35 were both committed AFTER the 07:00 London sweep on their
day. Each of those days is a sweep where Abyss would hold on an unwritten
placing while prod posted the placing behind it.

### Open item: prod watermark state

SSH to the gateway was refused by the session's permission classifier, so the
live state is unread. Command to run from the host shell:

```bash
ssh -i ~/.ssh/id_oci ubuntu@152.67.153.4 'D=/home/ubuntu/.local/state/dynamicalsystem/gazette; cat $D/watermarks.json; echo; tail -n 20 $D/watermarks.json.log'
```

Record here: the placing of every route, and the log lines since 2026-09-05.

## Orientation

### Why the targets drew level

The sweep has no invariant. Abyss's lead exists only because, on a day when
every review is written, all targets advance together and the initial offset
is preserved. The first day a review is late, Abyss holds and the followers do
not, so the offset collapses to zero. Once level, the offset never recovers:
every later sweep advances all targets together.

Reconstructed timeline (assumes Abyss started 2026-09-06 at 37 and prod at 38;
prod state will confirm or correct):

| Sweep (07:00 London) | Review state | Abyss | Prod |
|---|---|---|---|
| 09-06 | 37 written | posts 37, now 36 | posts 38, now 37 |
| 09-07 | 36 not yet written (16:53) | holds at 36 | posts 37, now 36 |
| 09-08 | 36 written | posts 36, now 35 | posts 36, now 35 |
| 09-09 | 35 not yet written (08:00) | holds at 35 | holds at 35 |
| 09-10 | 35 written | posts 35, now 34 | posts 35, now 34 |
| 09-11, 09-12 | 34 state unknown | | |

From 09-07 onward prod posted content the same day Abyss did, or a day before
Abyss could hold it back. The preview window was zero.

### Headroom for a manual bump

Reviews are `ok` down to placing 31. If the targets are level at 34 or 35,
decrementing Abyss by one gives it a lead with two or three written placings
still ahead of it, so it will not immediately hold again.

Two ways to "bump":

- **Skip** (runbook method): `Watermark.update()` on abyss only. Abyss never
  posts that placing; prod posts it tomorrow unseen. Fast, no code change.
- **Post**: publish the current placing to Abyss only, then decrement. Restores
  the lead honestly, but there is no single-target publish in the CLI today. A
  full manual sweep would also advance prod and defeat the purpose.

The skip costs one unpreviewed placing. The post costs a small CLI feature
(`gazette publish --only <route>`), which the fix below also benefits from.

### Design: a data-declared leader

Simon's concern is hardcoding target names. The relationship belongs in the
data, not the code: each follower route declares which route it follows.

```json
"josh": {
    "publisher": "Signal",
    "chart": "tQ26.H",
    "placing": 34,
    "target": "group....",
    "follows": "abyss"
}
```

Rule, evaluated per sweep with the leader's placing captured at sweep start:

> A follower may publish placing P only if its leader's placing at the start of
> the sweep is strictly less than P.

Consequences:

- **Level** (both at 34, review 34 written): leader start is 34, follower P is
  34, not strictly less. Follower holds. Abyss posts 34 and moves to 33. Next
  day the leader start is 33 < 34, so the follower posts 34. The lead is
  restored automatically. This is the "let Abyss pull ahead first" option and
  it is free.
- **Abyss holds on an unwritten review**: leader stays at P, follower is at
  P + 1. Tomorrow leader start P < P + 1, follower still posts P + 1 (already
  previewed). The day after, leader may still be at P and follower at P, so the
  follower holds. Followers can never draw level. This is the "stop prod
  drawing level" option, and it falls out of the same rule.
- **Abyss faulted**: followers stall until it recovers. Correct: prod never
  posts unpreviewed content.
- **Routes with no `follows`**: behave exactly as today. Abyss itself has no
  `follows`. No code path names any target.

Both of Simon's "two possibilities" are the same rule seen from different
starting states, so no choice between them is needed.

Validation at load: `follows` must name an existing route on the same chart,
and must not form a cycle. A bad value is a `ContentProblem`-style fault for
that route (held, alerted), not a crash of the sweep.

Alternatives rejected:

- Infer leadership from whichever route has the lowest placing: implicit,
  breaks silently the first time someone edits a placing by hand.
- Order routes in the JSON file and treat position as precedence: dict order is
  invisible in the file and does not survive a careless rewrite.
- A `role: leader` flag instead of `follows`: forces a single global leader.
  `follows` allows per-chart leaders and costs nothing extra.

## Decision

Pending. Proposed, awaiting Simon's call on:

1. Bump method now: skip (runbook) or post (needs `--only`).
2. Adopt the `follows` rule above as the invariant.
3. Whether `--only <route>` is in scope for this loop or a backlog item.

## Action

Not started.

## Outcomes

### Outcome 1: Abyss leads every prod target on tQ26.H again

Tests:
- [ ] Prod `watermarks.json` shows abyss placing strictly less than every
      other route on tQ26.H.
- [ ] `watermarks.json.log` records the manual change with a timestamp.
- [ ] A dry-run `gazette publish` on the gateway shows Abyss and prod would
      each publish a different placing on the next sweep.
- [ ] No prod target posted an unreviewed or unpreviewed placing as a result
      of the bump (Signal group history checked).

### Outcome 2: The sweep enforces the lead so prod targets cannot draw level

Tests:
- [ ] Unit test: leader and follower level, review written: leader publishes,
      follower holds.
- [ ] Unit test: follower one behind leader, both reviews written: both
      publish.
- [ ] Unit test: leader held on `ReviewNotReady`, follower one behind: follower
      publishes today, holds tomorrow when it would draw level.
- [ ] Unit test: `follows` naming a missing route, a route on another chart,
      or forming a cycle is held as a fault and alerted, and other routes still
      sweep.
- [ ] Unit test: routes without `follows` behave exactly as before.
- [ ] Runbook updated: the lead is enforced, the manual procedure is for
      recovery only.
- [ ] Deployed to the gateway with `follows` set on every prod route, and three
      consecutive scheduled sweeps show the lead preserved in
      `watermarks.json.log`.
