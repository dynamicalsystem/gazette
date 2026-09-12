---
loop: abyss-lead-invariant
product: gazette
owner: dynamicalsystem
status: Act
parent: null
blocked-by: []
worktrees: [abyss-lead-invariant]
prs: [https://github.com/dynamicalsystem/gazette/pull/7]
triggers: []
---

# Abyss lead invariant

## Status

Act

**Owner:** dynamicalsystem

## Context

Abyss is the preview target: it must always publish a placing one sweep before
every prod target so a bad review is seen there first. Simon fell behind on
reviews this week and the Abyss watermark stopped moving. The suspicion is that
the prod targets (e.g. Josh) have drawn level with Abyss, and that nothing in
gazette stops that from happening. Raised 2026-09-12.

Two asks came with the signal:

1. Restore the Abyss lead now if the chart has enough written reviews.
2. Design a fix so that, whenever a prod target has drawn level with Abyss,
   Abyss goes first on the next available turn, without hardcoding target
   names into the code. Drawing level is acceptable (clarified 2026-09-12);
   publishing a placing before or alongside Abyss is not.

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

### Prod watermark state (gateway, read 2026-09-12 ~12:00 UTC)

All four routes are on chart tQ26.H. Sweep runs at 06:00 UTC (07:00 London).

| Route | Publisher | Placing | Gap behind Abyss |
|---|---|---|---|
| abyss | Signal group | 33 | leader |
| josh | Signal number | 33 | 0 (level) |
| calendrical_rot | Signal group | 34 | 1 |
| bluesky | Bluesky | 36 | 3 |

`watermarks.json.log`, 2026-09-01 to 2026-09-12, abyss and josh only:

| Sweep (UTC) | abyss | josh |
|---|---|---|
| 09-01 to 09-04 | 43 -> 39, one per day | 44 -> 40, one per day (gap 1) |
| 09-05 | held at 39 (no log line) | 40 -> 39 (level) |
| 09-06 to 09-11 | 39 -> 33, one per day | 39 -> 33, one per day (level) |
| 09-12 | held at 33 | held at 33 |

Today's journal (`journalctl --user -u gazette-publish`): abyss and josh both
logged `Review tQ26.H.33 not written yet ... not ready, held`; bluesky posted
37 and calendrical_rot posted 35. Exit was clean, no fault, no alert. Image
revision running is 5b7c2c7.

Josh has received every placing from 39 to 34 on the same sweep as Abyss, six
days running. Review 33 was committed at 09:13 UTC today, after the sweep, so
tomorrow's sweep will post 33 to Abyss and Josh together unless something
changes before 06:00 UTC.

## Orientation

### Why the targets drew level

The sweep has no invariant. Abyss's lead exists only because, on a day when
every review is written, all targets advance together and the initial offset
is preserved. The first day a review is late, Abyss holds and the followers do
not, so the offset collapses to zero. Once level, the offset never recovers:
every later sweep advances all targets together.

The log shows exactly this. Abyss held at 39 on 2026-09-05 (review 39 not
written by 06:00 UTC). Josh posted 40 that morning and landed on 39, level.
From 09-06 both advanced together every day. The preview window for Josh has
been zero for a week. calendrical_rot and bluesky kept their gaps only because
they happened not to be one behind Abyss when it held.

### Headroom for a manual bump

Reviews are `ok` down to placing 31. Abyss and Josh are level at 33. Moving
Abyss to 32 gives it a lead of one with reviews 32 and 31 still ahead of it,
so it posts for two more days before holding at 30.

Two ways to "bump":

- **Skip** (runbook method): `Watermark.update()` on abyss only. Abyss never
  posts that placing; prod posts it tomorrow unseen. Fast, no code change.
- **Post**: publish the current placing to Abyss only, then decrement. Restores
  the lead honestly, but there is no single-target publish in the CLI today. A
  full manual sweep would also advance prod and defeat the purpose.

The skip costs one unpreviewed placing (33). The post costs a small CLI feature
(`gazette publish --only <route>`), which the fix below also benefits from.

There is a third way. The `follows` rule below self-heals the level case: if
it is deployed before tomorrow's 06:00 UTC sweep, Abyss posts 33 and Josh holds,
with no manual bump and no skipped placing. The bump is only needed as a
fallback if the fix cannot ship in time.

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
  P + 1. Tomorrow leader start P < P + 1, so the follower still posts P + 1
  (already previewed) and draws level at P. That is allowed. When review P
  lands, the level case above applies: Abyss posts P first, the follower holds
  that sweep and posts P the day after. A follower can draw level but can never
  publish a placing before, or on the same sweep as, its leader.
- **Abyss faulted**: followers stall until it recovers. Correct: prod never
  posts unpreviewed content.
- **Routes with no `follows`**: behave exactly as today. Abyss itself has no
  `follows`. No code path names any target.

Simon's clarified requirement is exactly the level case: drawing level is fine,
the leader must go ahead on the next available turn. The rule needs no
"never level" clause, which would have forced followers to hold a day early for
no preview benefit.

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

Agreed with Simon 2026-09-12:

1. Implement the `follows` rule from the Orientation and deploy before the
   2026-09-13 06:00 UTC sweep, so Abyss posts 33 and Josh holds. The invariant
   restores the lead by itself; no manual bump.
2. Fallback: if the image is not on the gateway by 05:30 UTC, skip Abyss from
   33 to 32 with the runbook procedure.
3. A single-route publish flag is out of scope; recorded in the backlog.

## Action

- [x] Branch `abyss-lead-invariant`; `follows` on `Watermark` with `leader_of`
      validation (`RouteInvalid`); sweep captures start placings and holds
      followers; nine unit tests; runbook and example updated.
- [x] PR #7 opened, offline-tests green, merged to main as 78777bd
      2026-09-12 15:24 UTC; branch deleted.
- [x] Release workflow run 34702130193 built the image from 78777bd.
- [ ] Add `"follows": "abyss"` to josh, calendrical_rot and bluesky in the
      gateway `watermarks.json` (SSH write blocked for Claude by the auto-mode
      classifier; Simon to run with a backup copy first).
- [x] Gateway auto-update pulled the new image 2026-09-12 15:28 UTC (id 887b9c196780, digest 2399fe865909).
- [ ] Dry-run `gazette publish` on the gateway: abyss would post 33, josh
      logs `waiting for the lead, held`, calendrical_rot 34, bluesky 36.
- [ ] Verify the 2026-09-13 06:00 UTC sweep in `watermarks.json.log`.

Pre-existing: ten tests in test_content and test_publishers need network
access and fail identically on main. CI runs the offline set only.

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

### Outcome 2: The sweep guarantees Abyss publishes a placing before any prod target does

Tests:
- [ ] Unit test: leader and follower level, review written: leader publishes,
      follower holds.
- [ ] Unit test: follower one behind leader, both reviews written: both
      publish.
- [ ] Unit test: leader held on `ReviewNotReady`, follower one behind: follower
      publishes today and draws level; when the review lands, the leader
      publishes and the follower holds that sweep, then publishes the next.
- [ ] Unit test: `follows` naming a missing route, a route on another chart,
      or forming a cycle is held as a fault and alerted, and other routes still
      sweep.
- [ ] Unit test: routes without `follows` behave exactly as before.
- [ ] Runbook updated: the lead is enforced, the manual procedure is for
      recovery only.
- [ ] Deployed to the gateway with `follows` set on every prod route, and
      `watermarks.json.log` over the following week never shows a follower
      advancing past a placing on or before the sweep its leader did.
