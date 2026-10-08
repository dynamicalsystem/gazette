---
loop: bluesky-url-replies
product: gazette
owner: dynamicalsystem
status: Decide
parent: null
blocked-by: []
worktrees: []
prs: []
triggers: []
---

# Bluesky URL replies

## Status

Decide

**Owner:** dynamicalsystem

## Context

Buy and Explore reviews carry a bandcamp `url` in the content JSON, but the
Bluesky posts never link to it. Readers who want to buy have to search. The
Bluesky publisher already contains an attempt at a link reply, but it is dead
code and has never fired. Simon opened this loop on 2026-10-08 with the
outcome: when the Bluesky route posts an Ignore review, the bot also replies
to the lowest-ranked Bluesky Buy|Explore review that has no URL reply yet,
with a post whose only content is the link preview card for the bandcamp URL.

## Observations

Evidence gathered 2026-10-08 from `main` at dd3c353, the content clone at
797b921, and the public Bluesky API (anonymous reads).

### Code

- `Bluesky.publish()` in `publishers.py` has a reply branch guarded by
  `verdict == "Buy." and hasattr(self.content, 'url')`. `self.content` is a
  `Review`, which exposes only artist/work/review/verdict, so the guard is
  always False. The body also uses `client_utils.TextBuilder` as a class, not
  an instance, and `.link('', url)` builds an empty-text facet rather than a
  link card. The branch is dead and, if reached, would raise.
- The review post text ends with the line `{chart}.{placing} - {verdict}`
  (`Publisher._formatter`). Every review post is therefore identifiable from
  its text alone.
- State: `watermarks.json` holds only `placing` per route. Post URIs are not
  recorded anywhere. The publish guard keeps `route:chart.placing` keys for
  24 hours only.
- `Bluesky.__init__` logs in before `publish()`; the 300-grapheme check runs
  on the review text in the constructor.
- A failed `publish()` (return False) holds the watermark, so the same review
  is posted again next sweep. A reply failure must not take that path.
- atproto 0.0.56: `Client.send_post(text, reply_to=, embed=)` accepts
  `AppBskyEmbedExternal.Main(external=External(uri, title, description,
  thumb))`. `title` and `description` are required strings, `thumb` is an
  optional blob ref. `Client.upload_blob(bytes)` exists. The SDK does not
  fetch link metadata; the caller must build the card.
- CI (`tests.yml`) runs four offline files only. `test_bluesky` performs a
  live login and is not in CI. There is no Bluesky mock in the test suite.

### Content

- tQ26.H: 100 items, `url` present on 93. All 93 are `*.bandcamp.com`.
  Verdicts after the 2026-10-08 pull: 29 Buy, 10 Explore, 48 Ignore, 13 blank.
- Older charts also carry `url`: tQ24.F (88 bandcamp + 1 other), tQ25.F
  (89 + 1), tQ25.H (89). The non-bandcamp URLs are one per chart.
- Written Buy|Explore items with no `url`: placings 91, 79, 77, 73, 21.
- bandcamp serves `og:title` ("CRONE, by One Leg One Eye"), `og:description`
  ("4 track album") and `og:image` to a plain HTTP client with a UA string,
  HTTP 200.

### Bluesky account (handle dynamicalsystem.com, did:plc:3sdo5wodzmtltyysmeynifk3)

- The last 200 feed items contain 90 tQ26.H review posts, placings 100 down
  to 11. Placing 11 (Ignore) was posted 2026-10-08. Placings 1-5 are unwritten.
- Of the posted Buy|Explore reviews, 38 have replyCount 0; 33 of those have a
  `url`. Lowest-ranked first the queue starts 94, 93, (91 no url), 90, 89.
- No review post has a reply from the bot. One hand-made reply exists, posted
  2026-07-14 on the first tQ26.H post (Serokolo 7, 2026-07-08): text is the
  empty string, no facets, embed `app.bsky.embed.external` with uri, title
  "Maramfa Musick Pro, by Serokolo 7", description "10 track album", and a
  thumb. That is the Bluesky app's rendering of bandcamp's OpenGraph tags,
  and the exact shape the outcome asks for.
- `replyCount` counts anyone's replies. Hey Colossus (2026-08-25) has one
  reply from a third party, so replyCount alone cannot mean "has a URL reply".
- Public reads (`getAuthorFeed`, `getPosts`, `getPostThread`) need no login.
  `getPosts` needs the DID form of the at-uri, not the handle.

## Orientation

**The dead branch answers the wrong question.** It tried to link the day's
own Buy post. The requested behaviour is a catch-up: on days when there is
nothing to link (Ignore), spend the spare post on an older Buy|Explore review.
That caps the account at two posts a day and keeps link cards in threads,
where Bluesky hides them from the main posts tab. Delete the branch rather
than repair it.

**Discovery should be stateless and read from Bluesky, not from local
state.** The 33 queued posts have no stored URIs, so a stored-URI design
cannot serve them. Scanning the account's own feed for `{chart}.{placing} -
Buy.|Explore.` and checking each candidate's thread for a self-authored reply
with an external embed is self-healing in the same way the follows rule is:
a reply deleted by hand is redone, a `url` added to content later is picked
up, and nothing new is written to `watermarks.json`. Cost is a feed scan plus
one thread read per candidate inspected, on Ignore days only.

**"Lowest ranked" means highest placing number.** Charts count down from
100, so the queue drains oldest post first (94 today).

**The queue will not clear within tQ26.H.** At most ten sweeps remain and
about half are Ignore, against 33 candidates. Either the rule carries into
later charts or the backlog is accepted. Under this rule, the Bluesky route's
current `chart` is the natural scope: once the route moves to the next chart,
tQ26.H posts stop being candidates. That is a deliberate trade: simple rule,
unlinked tail in every chart. Alternatives are a higher per-day cap until the
backlog clears, or a one-off manual catch-up. See A1 below.

**Link card construction is the only new external dependency.** Fetch the
URL, parse og:title, og:description, og:image, download the image, upload it
as a blob, build `External`. bandcamp cooperates with a UA. The failure modes
(4xx, missing tags, image too large) must not hold the watermark: the Ignore
post has already been delivered. A failed reply is logged as a fault and
alerted, but the sweep still advances. The next Ignore day retries the same
candidate.

**The 300-grapheme check does not apply** to a reply with empty text.

**Dry-run must stay offline for Bluesky.** The Validator should log the
reply it would make. Candidate selection and OG parsing should be pure
functions over fetched data so the offline CI subset can test them against
fixtures captured from the real feed and a real bandcamp page.

## Decision

Implement the outcome in the Bluesky publisher as a catch-up step that runs
only after a successful Ignore post:

1. Delete the dead reply branch.
2. Add `bluesky_links` (name provisional) with three pure functions:
   candidates from feed posts for a chart (lowest rank first, Buy|Explore,
   `url` present in content); has-link-reply from a thread view (any
   self-authored reply carrying an external embed); link card from a page's
   OpenGraph tags.
3. In `Bluesky.publish()`, when the verdict is Ignore and the post succeeded:
   scan the own feed (paginate until a placing below the chart's range is
   seen or the feed ends), walk candidates, skip any with a link reply,
   reply to the first remaining with `text=""` and the external embed.
   Return True regardless of reply outcome; surface a reply failure to the
   sweep as a fault so it alerts.
4. Validator logs `would reply to {chart}.{placing} with {url}` using the
   same candidate function over the public feed, or `no candidate`.
5. Offline tests for the three pure functions and for the fault isolation,
   added to the CI subset.

Assumptions needing Simon's confirmation before Act:

- **A1 Scope is the route's current chart.** Older charts' posts are never
  candidates, and the unlinked tail of a chart is accepted.
- **A2 One reply per Ignore sweep.** No burst to clear the backlog.
- **A3 Any `url` is linked, not only bandcamp.** OpenGraph parsing is
  generic; the one non-bandcamp URL per older chart would work the same way.
  tQ26.H has none, so this only matters under A1 if a future chart has one.

## Action

Not started.

## Outcomes

### Outcome 1: On an Ignore day, readers find a buy link under an older Buy|Explore review

Tests:
- [ ] Unit: given the captured feed fixture and tQ26.H content, candidates are
      [94, 93, 90, 89, ...] with 91 excluded for having no url.
- [ ] Unit: a thread fixture with a third-party reply only is not "linked";
      one with a self-authored external-embed reply is.
- [ ] Unit: the bandcamp page fixture yields title, description and image URL.
- [ ] Dry-run on a copy of the live data folder logs the intended reply target
      and URL, and touches nothing.
- [ ] Prod: after the first live Ignore sweep post-deploy, the lowest-ranked
      urlless tQ26.H Buy|Explore post has a reply from dynamicalsystem.com with
      empty text and an `app.bsky.embed.external` embed, and the Ignore review
      was posted and the watermark advanced.
- [ ] Prod: a Buy|Explore sweep produces no reply.

### Outcome 2: A reply failure never costs a review post

Tests:
- [ ] Unit: with the link-card fetch failing, `publish()` returns True and the
      failure is recorded as a fault.
- [ ] Prod log: a sweep with a reply fault alerts and the watermark log shows
      the advance.

### Outcome 3: The dead branch is gone and Buy|Explore days are unchanged

Tests:
- [ ] `grep -n "hasattr(self.content, 'url')"` finds nothing.
- [ ] Existing publisher tests pass.
