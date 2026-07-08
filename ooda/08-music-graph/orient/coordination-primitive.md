# Orient: the coordination primitive (a "muster")

Captured 2026-07-08. Resolves the "where does the canonical record live" fork left
open in `../observe/gig-coordination-journey.md`, and generalises the gig case into a
reusable primitive. Working name: **muster** (assemble a list of people to a place, at a
time, with a transaction chain). Rename at will.

## The generalisation

Gig-coordination is one instance of a general shape:

> **Herd a list of cats to a locus at a moment, with a transaction chain.**

Instances already live across the estate -- so this is earned by three real cases, not
premature abstraction:
- **gazette** -- gigs (band -> venue, time, ticket money).
- **runclub** -- group runs (meet point, time; transaction chain often empty, or a race fee).
- **festers** -- festival meetups (venue/stage, set time; shared costs).

## The decision: service is truth, chat is a comms adapter

The canonical workflow + structured data live in a **dynamicalsystem service** -- a
`group_cap`-gated private record (the "atproto/HMAC group" from `identity.md`). The
group chat (Signal/WhatsApp/...) is **not** the medium; it is a **pluggable comms
adapter**. This resolves the journey's fork decisively:

- **Truth** -- in the service (single source; editable in place; multi-channel;
  web-viewable). No more copy-paste-edit-repost.
- **Interaction stays in the chat** -- the adapter is **bidirectional**: notifications
  and nudges go *out*; reactions/replies come *in* and update the record. This honours
  "people want it managed for them, not another app to tend" -- they never have to leave
  the chat for the common path.
- **Depth on the web** -- `gazette.dynamicalsystem.com` renders the record's private
  group page for when someone wants detail (full ledger, history).

Three surfaces, one truth: **service = truth, chat = low-friction interaction, web =
depth.**

## Components of a muster

```
muster {
  roster:      [ user_key, ... ] with per-person state      ← who (identities from identity.md)
  locus:       place / venue / meet-point                   ← where
  moment:      datetime (UTC canonical)                      ← when
  txn_chain?:  per-person ledger owes -> paid -> released    ← OPTIONAL money/obligation flow
  state:       PROPOSED..GATHERING..COMMITTED..SETTLING..SETTLED..DONE  (+ reminders)
  comms:       [ adapter, ... ]  (Signal now; pluggable)     ← how it reaches people
  anchor?:     a graph object (band / route / festival)      ← the ligand that convened it
}
```

- **txn_chain is optional.** A group run to a meet-point may have no money at all; a gig
  has ticket money; a festival meetup has shared costs. The transaction chain is a facet,
  not the spine.
- **roster entries are `user_key` identities** (or, pre-identity, just chat handles that
  upgrade to `user_key` on first magic-link).
- **anchor** is the band/route/festival the muster hangs off -- "bands are ligands"
  (observations section 2) generalised to "the thing that convened us."

## Membrane placement

- The **roster + txn_chain are cytoplasm** -- private to the group (`group_cap` vesicle).
  The money/obligation ledger never leaves.
- The **fact "attended <anchor> at <locus> on <moment>"** can be **transcytosed to public
  history** -- becoming the fan's public graph facet. Coordination produces the private
  ledger *and* the public attendance history from one act.

## Why this is the estate's shared service

A muster service on the identity substrate is the concrete tie between the three apps:
gazette/festers/runclub each become **feeders + instantiators** of musters rather than
separate coordination silos. It is also the first place the abstract "graph" earns its
keep operationally -- musters *are* edges (people x objects x place x time) accreting into
the graph as a byproduct of real use.

## Call-outs (unchanged / reinforced)

- **Claimed, not verified.** The txn_chain records what people *said*; money moves
  off-service. Not a payment processor. (See journey doc.)
- **Signal-first comms adapter.** gazette's signal-cli path makes Signal feasible now;
  WhatsApp has no open bot path. Adapters are pluggable, but the beachhead is Signal.
- **Bidirectional adapter is the hard/novel bit.** Notify-out is shipped-adjacent
  (gazette publishes). Ingest-in (parse reactions/replies -> state transitions reliably)
  is the new capability -- gazette's `_drain_inbox`/receive is the seam to build on.

## Cross-references
- **this loop** `identity.md` -- `group_cap` = the muster's private compartment; `user_key`
  = roster identity. `../observe/gig-coordination-journey.md` -- the lived instance this
  generalises (fork now resolved here). `../observe/observations.md` -- membrane (3),
  ligands (2).
- **gazette** `publishers.py` -- Signal send + `_drain_inbox` receive = the comms adapter seam.
- **festers**, **runclub** -- the other two instantiators (festival meetups, group runs).
