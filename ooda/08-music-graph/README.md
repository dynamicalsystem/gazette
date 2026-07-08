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
begun on the identity substrate: [`orient/identity.md`](orient/identity.md) -- the HMAC
capability hierarchy, the "wrong level" festers fix, and the seed-derivation fork
(leaning pure-derivation). Act (the first spike) follows.

## Candidate first experiment (to confirm in orient)

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
