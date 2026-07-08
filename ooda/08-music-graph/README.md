# Loop 08: music graph (a semi-permeable, PII-free social graph)

## Status: [~] observe

A new arc, distinct from the (now complete) gazette cloud refactor. The front door
is `gazette.dynamicalsystem.com` and the home is gazette's loop-06 serve skeleton,
but the vision spans repos: gazette + festers feed the graph, runclub supplies the
privacy lineage.

## Vision (one paragraph)

People catalogue and map their musical experiences across live (gigs, festivals) and
recorded media. "I liked band X after a dynamicalsystem post on Bluesky -> give me a
dynamicalsystem id -> show me the graph of gigs + content for that band -> let me
express geographic preferences **in private** and find folk with the same interests
**in public**." A **semi-permeable, PII-free** graph of bands, recordings, gigs,
venues, festivals, promoters, fans, labels, publications and other networks -- where
some facets are public and discoverable and some are private, with a controlled
membrane between them.

## Phase

We are in **Observe -> Orient**. The synthesis, model, state-of-the-art, and open
questions are in [`observe/observations.md`](observe/observations.md). Orient has
begun on two fronts: [`orient/identity.md`](orient/identity.md) -- the HMAC capability
hierarchy, the "wrong level" festers fix, and the seed-derivation fork (leaning
pure-derivation); and [`orient/coordination-primitive.md`](orient/coordination-primitive.md)
-- the generic "muster" (herd a roster to a locus at a moment with an optional transaction
chain), with the decision that **the service is truth and the chat is a pluggable comms
adapter**. Act (the first spike) follows.

**Anchoring use case:** [`observe/gig-coordination-journey.md`](observe/gig-coordination-journey.md)
-- a lived workflow (coordinating gig attendance + payment in a private group chat) that
grounds the whole arc and reframes the likely v1 wedge: a **coordination assistant in the
group chat you already use**, with the graph/history/matching emerging as a byproduct.
Notably its nearest slice is buildable on gazette's *existing* Signal machinery -- no
PDS/ZK/atproto required.

## Act so far

- **[x] Signal-muster receive spike** (2026-07-08) -- **success**. Publishing a muster and
  folding Signal reactions into a live roster+ledger works end to end on gazette's Signal
  path. Findings + the one architectural constraint (a persistent websocket listener is
  required; json-rpc drops messages with no client attached) in
  [`act/spike-signal-receive.md`](act/spike-signal-receive.md). This is the "ingest-in"
  seam the muster needs, proven with no PDS/ZK/atproto.

## Later experiment (the novel core)

The **"glucose transporter"** spike: two fans, one private facet ("near Manchester"),
one public interest ("follows band X") -> the server surfaces a **mutual opt-in match**
revealing only the match, not the facets. Built **trusted-server first** (non-ZK); the
runclub ZK design is the hardening target, not the v1 build. This is the one piece the
atproto ecosystem is *not* building for us.

## Cross-references

Full list with URLs in `observe/observations.md`. In brief:

- **festers** `festers/accounts.py` -- the HMAC, zero-PII magic-link identity to reuse.
- **runclub** `atproto_private_proposal.md` + `zk-group-interaction.svg` -- our prior
  no-trust ZK private-content design (the north star for the sharing layer).
- **gazette** loop 06 serve skeleton (the web home) + the `content` repo corpus
  (object-graph seed: bands / recordings / Quietus reviews).
- **atproto** private-data frontier (WG, buckets, namespaces, Stratos) -- all
  trust-the-PDS; none build the matching membrane.
