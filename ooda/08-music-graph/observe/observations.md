# Observe: the semi-permeable music graph

Captured 2026-07-08. A synthesis of the riff + a scan of the atproto private-data
frontier + our own prior work. This is Observe, not a decision.

## 1. The product

A PII-free graph for cataloguing and mapping musical experience across live and
recorded media. Canonical user story:

> "I liked band X after a dynamicalsystem post on Bluesky. Give me a dynamicalsystem
> id. Show me the graph of gigs + content for band X. Let me express geographic
> preferences **in private**, and find folk with the same interests **in public**."

Entity kinds: bands, recordings, gigs, venues, festivals, promoters, fans, labels,
publications, other social networks. Fans attach to objects with typed edges (saw,
follows, likes, discovered-via).

## 2. The model: a tissue, not a bag of cells

The real world is messy: artists have unlinked pseudonyms, collabs are uncredited,
much is inferred, lots is circular. So **it is not a DAG, and there is no hub** --
just nodes. But the nodes are **not uniform**:

- **Object nodes** (bands, recordings, gigs, venues, labels, publications) =
  **extracellular matrix**: fully public, no private interior, the shared scaffold.
  Half of it is already ours to seed (see 7).
- **Fan nodes** = **cells**: a public surface + a private cytoplasm + a **membrane**.
- **Bands are ligands**: the extracellular signal that binds a fan's receptors and
  makes them show up and cross something. "Bands drive the people" = bands are
  signalling molecules, not a hub. This resolves the "no hub" intuition: hub-less for
  cells, but the matrix is a shared scaffold every cell touches.

What people care about is **themselves and the experience** -> the cytoplasm (private
experiential graph: my gigs, my listening, my geo); the surface is minimal public
projection.

## 3. The membrane: blood-brain-barrier as the design spec

The public/private boundary is a **semi-permeable membrane**. BBB transport biology
maps onto it, and each mechanism is a design decision:

| BBB mechanism | Crosses | Privacy-membrane analogue |
|---|---|---|
| Tight junctions | nothing paracellular | **Default-deny**: private by default; nothing crosses without a named mechanism |
| Passive lipophilic diffusion | small non-polar (ethanol, LSD) | **The leak we're weak to**: low-entropy quasi-identifiers, individually innocuous, cross uncontrolled, **aggregate** into identity. Budget the cumulative dose (k-anonymity / leakage budget) |
| Facilitated transport (GLUT1/glucose) | one specific, saturable substrate | **The matching transporter**: a match is a *derived, minimal* signal ("you two overlap"), not raw data. Substrate-specific + rate-limited or it becomes an enumeration oracle |
| Transporter hijack (L-DOPA rides LAT1) | a prodrug in a substrate's coat | **The attack**: craft inputs to ride the match channel and extract more than intended |
| Receptor-mediated transcytosis (transferrin) | large proteins, active, energy-dependent | **Explicit rich disclosure**: heavy private records cross only by binding a specific receptor (per-instance consent) with friction. Never passive |
| P-glycoprotein efflux | pumps xenobiotics back out | **Revocation**: pump a disclosure back -- best-effort (caches persist like metabolites) |
| Osmotic opening (mannitol) | everything, transiently | **Linkage / breach**: junctions pop open under a hypertonic solvent |

Two load-bearing consequences:

- **Federation is osmotically corrosive.** "Other social networks" is the hypertonic
  solvent: cross-referencing dynamicalsystem public facets against someone's
  Bluesky/Last.fm graph is the mannitol that opens the junctions. The atmosphere's
  thesis is federation; the membrane is most weak to it. Not a bug to fix -- a
  tradeoff to *tune*: how lipophilic do we let public facets be.
- **The glucose (the only thing allowed facilitated across) is a *match event***, not a
  fact -- "you two overlap on X, both opted in." Anything richer is forced through
  receptor-mediated (explicit) transport. Open question: is there a second admissible
  substrate -- an *introduction* that opens a thin receptor channel post-match?

## 4. The three layers

| Layer | Metaphor | Build stance |
|---|---|---|
| Public graph + identity (DID) | extracellular matrix + cell surface | **Lean on atproto** -- real, shipped |
| Private store + share-with-group | cytoplasm + vesicles | **Build our own now** (festers-style / runclub-ZK); migrate to atproto buckets *if* they ship -- do not block on an unshipped, contested spec |
| **Semi-permeable matching** | **glucose transporter** | **Invent it** -- distinctive core, no upstream anywhere |

## 5. State of the atproto private-data frontier (Spring 2026)

Two schools:

**A. Trust-the-PDS (the WG consensus, unshipped).** Access control applied by the PDS;
"encryption at rest is not a goal." All are ACL-gated *sharing*:
- **Bryan Newbold** -- namespace model: public repo is a special always-public
  namespace; private namespaces alongside, DB-backed, gated by scope + DID.
- **Daniel Holmgren (dholms)** -- *buckets*: a named container of records with a single
  authoritative ACL (rejected his earlier coarse "realms").
- **Kandake (ashex, Northsky)** -- *Stratos*: `boundary`-scoped private records; "trust
  the platform," explicitly not E2EE.
- **Boris Mann (@bmann.ca)** runs the community/WG space (the "privacy room"); his own
  framing states the trust-the-PDS premise plainly.
- Status: proposal phase, competing approaches, "significant experimentation before
  finalized," a Bluesky focus through summer 2026.

**B. No-trust ZK (ours, prior work in runclub).** `atproto_private_proposal.md`:
encrypted content on the Firehose + zero-knowledge access control; groups as
cryptographic commitments (`hash(master_secret + member_DIDs)`, no central roster);
per-member secret `HMAC(master_secret, member_DID)`; unlinkable proofs; a ZK Auth
Service that cannot link users to groups. Stronger than "own the PDS": the PDS never
holds cleartext or membership.

## 6. The gap neither school fills

Both schools -- including **our own** runclub proposal -- solve **sharing among people
who already found each other**. runclub's flow assumes Alice *already knows* her group
("Close Friends = [Bob, Charlie, Dave]") and hand-delivers member secrets out-of-band.
That is receptor-mediated transcytosis (pre-formed, pre-keyed group).

The music-graph membrane needs the **glucose transporter**: two **strangers** discover
they both privately like band X, near each other, with **no prior shared secret**,
revealing nothing else. That is **private set intersection / anonymous matchmaking** --
a different primitive. runclub only *gestures* at it (Future Extensions: "anonymous
groups where even members don't know each other"). **It is unclaimed by the WG and by
us.** It is the distinctive thing to invent.

But the runclub design hands us the **toolkit**: commitments, unlinkable ZK proofs, and
**HMAC pseudonyms -- the exact primitive already in festers `accounts.py`**. The crypto
lineage is consistent across runclub -> festers -> here.

## 7. What we already own (seeds)

- **Object graph (recorded side)**: the `content` repo -- 5 Quietus charts
  (`tQ24.F/H`, `tQ25.F/H`, `tQ26.H`), a few hundred `{place, artist, work, review,
  verdict}` records -> Band / Recording / Publication / verdict nodes for free.
  `series.json` is a (stale) chart registry.
- **Object graph (live side)**: festers -- festivals, venues, travel matrices, events
  -> Gig / Venue / Festival / Promoter nodes.
- **Identity + private primitive**: festers `accounts.py` -- HMAC(secret, email-or-phone)
  pseudonym, zero PII, out-of-band token credential. Directly reusable as the
  "dynamicalsystem id" private root.
- **Web home**: gazette loop-06 serve skeleton behind caddy; `gazette.dynamicalsystem.com`
  is a caddy route + endpoints.
- **Deploy substrate**: tinsnip quadlets on the gateway. A dynamicalsystem-run PDS would
  be a new quadlet here.

## 8. The lineage (why this is not new)

> **runclub** (runner GPS -- hypersensitive location) -> **festers** (festival location
> -- weak correlation to residence; the temporal absence-inference needs the
> `(residence, user_id)` key we never hold) -> **the music graph**.

A three-project arc circling *PII-free, location-aware social*. festers is the right
place to start the private-facet work: the private data there is naturally benign.

## 9. Stances taken in the riff (candidate, for orient)

- **Reject trust-the-PDS.** It only collapses to "trust a platform" when the PDS is
  someone else's business. Terminus: either a **dynamicalsystem-run PDS** (legible,
  accountable trust) or the **runclub ZK** posture (no cleartext to trust).
- **Identity = HMAC-pseudonym private root + optional DID public projection** (the
  membrane is the mapping). Start with the Signal/email audience (no atproto onboarding
  friction), grow into the public atmosphere without re-platforming identity.
- **v1 crypto is boring on purpose.** Prove the product with a trusted server-side
  matcher; invest in ZK/PSI only if the matching sings.

## 10. Open questions (for orient)

1. Is the admissible "glucose" only ever a match event, or also an *introduction*
   (a thin receptor channel that opens post-match)?
2. Is a "follow" a public membrane-surface act (freely diffusing) or cytoplasmic until
   actively transcytosed? (This sets where the whole barrier sits.)
3. Self-hosted dynamicalsystem PDS vs runclub-ZK-first for the private layer -- or
   trusted-server-now with a clean interface to both?
4. Who is the "evolved PDS" person from Boris Mann's Discord privacy room? (substance
   recovered; name still unknown -- Discord is unreachable from here.)
5. First hub for v1: Band (discovery anchor) vs the fan's own timeline?

## Cross-references

### Internal (dynamicalsystem repos)
- **runclub** `atproto_private_proposal.md` -- no-trust ZK private-content design (north
  star for the sharing layer); `zk-group-interaction.svg` -- the Alice/Bob/ZK flow.
- **festers** `festers/accounts.py` -- HMAC zero-PII magic-link identity (email + phone);
  the reusable private-root primitive.
- **gazette** `ooda/06-service-skeleton/` -- the serve skeleton (web home); this repo's
  `content` sibling -- the object-graph seed corpus + `series.json`.
- **festers** `data/festivals/<id>/schedule.json`, `docs/` -- the live-side object seed.
- **tinsnip** `hosts/gateway/` -- deploy substrate for a future dynamicalsystem PDS.

### External (atproto private-data frontier, read 2026-07-08)
- Permissions spec -- https://atproto.com/specs/permission
- 2026 Spring roadmap -- https://atproto.com/blog/2026-spring-roadmap
- Daniel Holmgren, "Permissioned Data Diary 2: Buckets" -- https://dholms.leaflet.pub/3mfrsbcn2gk2a
- Kandake / ashex, "A Model for addressing privacy on ATproto" (Stratos) -- https://chipnick.com/a-model-for-addressing-privacy-on-atproto/
- Bryan Newbold namespace model, via Private Data WG notes -- https://notes.commonscomputer.com/s/atproto-private-data-wg
- Private Data Working Group wiki -- https://atproto.wiki/en/working-groups/private-data
- Boris Mann, atproto community resources -- https://bmannconsulting.com/notes/atproto-community-resources/
- Paul Frazee on Bluesky + atproto (SE Radio 651) -- https://se-radio.net/2025/01/se-radio-651-paul-frazee-on-bluesky-and-the-at-protocol/
- "Private, non-shared data in repo?" (atproto discussion #3363) -- https://github.com/bluesky-social/atproto/discussions/3363
