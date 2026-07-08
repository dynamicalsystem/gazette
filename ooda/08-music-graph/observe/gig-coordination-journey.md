# Observe: the gig-coordination user journey

Captured 2026-07-08. A lived workflow (SH's own), documented as a **target user
journey** -- several loops away, but it grounds the whole music-graph arc in a
concrete job-to-be-done, and it reframes the likely v1 wedge.

## The lived reality (current, manual)

People go to gigs *with people*, and those people are already in a private group
(Signal, WhatsApp). Today SH runs the coordination by hand:

1. **Propose** -- post a gig to the group (it is literally one of the gazette Signal
   targets): `(band, date/time, location, price)`.
2. **Gather** -- people reply/react; an **attendee list** forms.
3. **Book** -- tickets get booked (by the organiser).
4. **Settle** -- the message is **copied, edited, re-pasted** with a state change:
   *monies owed* (per attendee).
5. **Pay** -- people **react to the post** after transferring cash; the record is
   updated to *paid*.
6. **Release** -- sometimes tickets are distributed (email, DICE transfer, ...) --
   an **off-group** transaction the record only references.
7. **Remind** -- nearer the gig, memory is **lossy**, so the whole thing is **reposted**
   `(band, date/time, location, price, attendees, state)` to jog everyone.

The record is a **living, stateful object** currently implemented as copy-paste-edited
chat messages. "It would be great if some service handled all this" -- and note the
tone: people *want it managed for them*, not another app to tend.

## The record + its state machine

Gig-coordination record (private to the group):
`{ band, datetime, venue/location, price, organiser, attendees[], per-attendee: {in?, owes, paid?}, ticket-release-status, state }`

```
PROPOSED ─→ GATHERING ─→ BOOKED ─→ SETTLING ─→ SETTLED ─→ RELEASED ─→ REMINDED ─→ ATTENDED
   post      replies/     tickets   monies      all       tickets     pre-gig     graduates to
   to group  reactions    bought    owed        paid       out         reposts     public history
             = attendee   (organiser)          (reactions  (off-group)
               joins                             = paid)
```

Inputs are **chat-native reactions/replies**: a reply is "I'm in"; a reaction is
"I paid." Outputs are **reposts** -- an updated snapshot pushed back to the chat.

## How it lands on the model (why this is the same project)

- **The group is a `group_cap` vesicle.** The gig record lives in a private group -- the
  exact "bearer key to a private group" from `../orient/identity.md`. Attendance +
  payment state is **cytoplasm**.
- **The gig is a stateful graph object anchored on a band** -- "bands are the ligands"
  (observations section 2) is literally true here: the band is why the post happens.
- **The membrane is right here.** The payment ledger stays private (cytoplasm); the bare
  fact "I saw band X at venue Y on date Z" can be **transcytosed to public history** --
  which *is* the fan's public content graph. Coordination produces both the private
  state and the public attendance history, for free.
- **gazette already does the hard half.** gazette publishes to these Signal groups today
  and has a Signal HTTP client that can **receive/drain** (read reactions). A gig record
  is a review record's interactive, stateful cousin -- same publish machinery, plus a
  read loop and a state model. The reminder-repost is a scheduled re-publish (gazette
  already has the scheduler pattern).
- **festers is the sibling, not a stranger.** festers = "which of many events should I
  see" (optimisation); this = "let's go to this one together and sort the money"
  (coordination). Shared vocabulary: events, venues, times, attendance, groups.

## The reframing (the important bit)

I had framed v1 as a *personal cataloguing tool*. This journey is a **sharper wedge**:

> a **gig-coordination assistant that lives in the group chat you already use**, owning
> the `(band, when, where, price, who's-in, who's-paid, remind-me)` lifecycle.

It is better because: the pain is **felt and recurring** (SH does it by hand every
time); it is **native to an existing channel** (no "come to our app"); it is **viral
within a group** (everyone benefits at once, zero network effect needed); and it
**generates the graph as a byproduct** -- attendance, bands, venues, history accrue
*without anyone "cataloguing" anything*. Coordination-first, graph-emergent. The
insight/history/matching layers become the reward on top of a tool people already want.

## Boundaries to respect (call-outs, not decisions)

- **Claimed state, not verified money.** Payment is self-reported via reactions and the
  cash moves off-group. The service tracks *what people said*, it does **not** move or
  verify money. Do **not** drift into being a payment processor / escrow -- that is a
  trust + regulatory minefield. It is a coordination aid over a claimed ledger.
- **Signal first; WhatsApp is a cliff.** gazette already lives in Signal (signal-cli),
  so a Signal bot-in-group is feasible. WhatsApp has no comparable open bot path (Business
  API or nothing). "Same experience across chats" is aspirational; Signal is the beachhead.
- **Where does the canonical record live?** [RESOLVED in `../orient/coordination-primitive.md`]
  Not the chat. Truth lives in a **dynamicalsystem service** (a `group_cap`-gated record);
  the chat is a **pluggable, bidirectional comms adapter** (nudges out, reactions in), and
  the web is depth. This also generalises the gig into a reusable "muster" primitive
  (roster + locus + moment + optional transaction chain) shared across gazette/festers/runclub.

## Nearest buildable slice (when this arc opens)

Most of this is far off, but the **nearest** piece is unusually close to shipped gazette:
publish a **structured gig record** to a Signal group, **read reactions** to maintain an
attendee + paid ledger, and **repost an updated snapshot** on a schedule / on state
change. That is gazette's existing publish + receive + schedule machinery, plus a state
model -- no PDS, no ZK, no atproto required. It could be an early, standalone win that
starts generating real graph data long before the membrane/matching layers exist.

## Cross-references
- **gazette** `gazette/src/dynamicalsystem/gazette/publishers.py` -- the Signal client
  (send + `_drain_inbox` receive) this would extend; the Signal targets are today's groups.
- **this loop** `../orient/identity.md` -- the gig record's group is a `group_cap` vesicle;
  attendees are `user_key` identities. `../observe/observations.md` -- membrane (3),
  bands-as-ligands (2), the runclub->festers->graph lineage (8).
- **festers** -- the multi-event optimisation sibling of this single-event coordination.
