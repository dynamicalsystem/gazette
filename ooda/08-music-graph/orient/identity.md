# Orient: the dynamicalsystem identity substrate

Captured 2026-07-08. Moves the identity question from Observe toward a decision.
The (a)/(b) fork is left OPEN, but with a recorded lean and its reasoning.
Supersedes the "identity stance" bullet in `../observe/observations.md` section 9.

## 1. The capability hierarchy

Identity is an HMAC capability tree, not an account record. One private root per
person; apps and disclosures hang off it as derived keys.

```
ROOT_SECRET (dynamicalsystem-held, one secret)
   │
   ▼
user_key = HMAC(ROOT_SECRET, contact)         ← your dynamicalsystem PRIVATE DATA KEY
   │   • the private root, stable across festers / gazette / runclub
   │   • delivered once by magic-link over ANY channel (Signal / Bluesky DM / Reddit / X / email)
   │   • the channel is only a delivery mechanism; after minting, the key is the identity
   ├── group_cap  = HMAC(user_key, group_id)   → shareable bearer key to a PRIVATE group
   │                  (a festers plan, a runclub route)         ← vesicle / bucket capability
   └── public_cap = HMAC(user_key, "public")   → shareable bearer key to your PUBLIC content
                      (festers history, liked gazette reviews)  ← membrane-surface receptor

PUBLIC identity = <handle>.dynamicalsystem.com  (atproto handle/DID) — "log in with this"
```

Membrane mapping (see `../observe/observations.md` section 3): root key = cytoplasm;
`public_cap` = surface receptor; `group_cap` = a bearer capability for a vesicle; the
atproto handle = the cell's public address. Same HMAC primitive as runclub's
`member_secret = HMAC(master_secret, member_DID)` -- one crypto spine across the estate.

Derived caps are **bearer capabilities**: possession grants access. So they need
least-privilege scoping and rotation/revocation (festers already rotates tokens --
same pattern). `group_cap` is the sensitive one (grants private-group access).

## 2. The one unavoidable mapping (and it is opt-in)

Pure derivation removes the *channel* table (see fork below), but linking a **public
atproto DID** to a private root is a genuine stored mapping: a `did:plc` handle is
externally assigned, not derivable from an HMAC. This `DID <-> user_key` map IS the
public/private membrane. It is:
- **opt-in** -- only exists for users who choose a public presence;
- **minimal** -- one row per public user, no contact data;
- **the** thing to protect, because it is the linkage the whole design guards.

## 3. The "wrong level" fix (festers)

festers today derives the id from **(festival_id + contact)** -> a *per-festival*
pseudonym. That is the wrong level. Wind it back:
- `user_key = HMAC(ROOT_SECRET, contact)` is the root (user-level, app-agnostic);
- a festers plan is a **derived cap under it**: `HMAC(user_key, festival_id)`;
- runclub routes, gazette likes: same shape.

The user is the root; apps hang capabilities off it. (This is a festers refactor --
see section 6; do not do it until this substrate is agreed, to avoid re-doing it.)

## 4. The fork: how is user_key seeded? [OPEN -- leaning (a)]

### (a) Pure derivation -- `user_key = HMAC(ROOT_SECRET, contact)`  [current lean]
Identity *is* the HMAC of the contact. Zero standing state.

Case for (a) (SH, 2026-07-08):
- Once the id is minted it is **not tied to the comm channel** -- the channel only
  delivered the link once; the key is the identity thereafter.
- We do **not** need to send the same HMAC to multiple places.
- (b)'s channel table is an **attack vector** -- a `fingerprint(contact) -> user_key`
  map is exactly the cross-channel linkage this whole design exists to avoid; a breach
  of it is an osmotic deanonymisation.
- (b) needs a **serverside "link a new channel" flow** in the context of an
  already-linked channel -- extra surface (confused-deputy / session-fixation /
  phishing the link step) for little gain.

Honest cost of (a) (recorded so the fork is not one-sided):
- **Change of contact = new identity.** Switch phone number, or move Signal->Bluesky,
  and you get a different key -> a different person; your graph does not follow you.
- Mitigation that keeps (a)'s no-standing-table property: an **opt-in, user-driven
  re-key migration** -- prove control of the old key (you hold it) + verify the new
  contact, then re-home data old_key -> new_key in one authenticated operation. A rare,
  explicit event, not a standing channel table.
- Recovery is a non-issue under (a): derivation is deterministic, so "recover" = request
  a fresh link on the same channel; no account-recovery flow needed.

### (b) Random root + bound contacts
`user_key` minted once (random); each verified channel stores
`HMAC(ROOT_SECRET, contact) -> user_key`. One identity, many channels, still PII-free
(only fingerprints stored). Rejected-leaning for the reasons in (a)'s case: the standing
map is a honeypot and the linking flow is a bad surface.

## 5. Trust reality

A single `ROOT_SECRET` means **dynamicalsystem can derive every user_key**. This is
**trust-the-operator**, not zero-knowledge -- consistent with the "trust the PDS if it
is mine" stance (see observations section 9), and fine for v1 on our own audience. The
runclub ZK design (`runclub/atproto_private_proposal.md`) is the no-trust hardening path
for when the stakes rise: commitments + unlinkable proofs remove the operator's ability
to derive/link. Named as a choice, not an accident.

## 6. Spawned Act loops (once this substrate is agreed)

This is a cross-cutting interface (festers + gazette + runclub bind to it), so per the
house rule it is called out before change:
- **festers refactor** -- wind the HMAC back to user-level (section 3); plans become
  derived caps. First concrete Act.
- **shared `identity` service** -- externalise the mint/derive/verify + magic-link
  delivery (multi-channel) so all three apps call it, rather than each re-implementing
  festers' `accounts.py`.
- Both gated on this doc reaching a decision (esp. the (a)/(b) fork).

## Cross-references
- **festers** `festers/accounts.py` -- current HMAC magic-link auth (the wrong-level id
  to refactor); `_PHONE_RE` / `normalize_phone` already support phone (Signal) delivery.
- **runclub** `atproto_private_proposal.md` -- `member_secret = HMAC(master_secret,
  member_DID)` is the same primitive; the ZK design is the no-trust future.
- **this loop** `../observe/observations.md` -- sections 3 (membrane), 4 (layers),
  9 (stances this supersedes).
