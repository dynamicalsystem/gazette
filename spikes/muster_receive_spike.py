#!/usr/bin/env python3
"""Spike: drive a "muster" off gazette's Signal receive path.

Loop 08 (music-graph) first Act. Goal: prove we can (1) publish a structured muster
post to Signal, (2) read reactions/replies back via /v1/receive, (3) correlate them to
the muster by the sent message's timestamp, and (4) fold them into a roster + ledger.

Throwaway spike -- self-contained (just `requests`), reads SIGNAL_URL / SIGNAL_IDENTITY
from env (source gazette.prod.env for the live gigbot over WireGuard). NOT wired into
the package. The receive endpoint is DESTRUCTIVE (consumes the queue) -- do not run
during a prod publish.

Usage:
    source ~/.local/share/dynamicalsystem/config/gazette.prod.env   # SIGNAL_URL=WG, gigbot
    python spikes/muster_receive_spike.py send <target> "Muster: <band> ..."
    python spikes/muster_receive_spike.py raw                       # dump the raw receive queue
    python spikes/muster_receive_spike.py watch <muster_timestamp>  # poll + fold reactions

Reaction convention (spike): any reaction => "in" (join roster); a money emoji
(£/$ / 💷💰💵 / ✅) => "paid". Removing a reaction => leave.
"""
import json
import os
import sys
import time

import requests

SIGNAL_URL = os.environ.get("SIGNAL_URL", "").rstrip("/")
IDENTITY = os.environ.get("SIGNAL_IDENTITY", "")
PAID_EMOJI = {"💷", "💰", "💵", "✅", "£", "$"}

if not SIGNAL_URL or not IDENTITY:
    sys.exit("set SIGNAL_URL and SIGNAL_IDENTITY (source gazette.prod.env)")


def send(target: str, text: str) -> None:
    r = requests.post(
        f"{SIGNAL_URL}/v2/send",
        json={"message": text, "text_mode": "styled", "number": IDENTITY,
              "recipients": [target]},
        headers={"Content-Type": "application/json"}, timeout=60,
    )
    print(f"HTTP {r.status_code}")
    try:
        body = r.json()
    except ValueError:
        body = r.text
    print(json.dumps(body, indent=2, ensure_ascii=False))
    ts = body.get("timestamp") if isinstance(body, dict) else None
    if ts:
        print(f"\n>>> muster timestamp = {ts}")
        print(f">>> next: python {sys.argv[0]} watch {ts}")


def receive() -> list:
    r = requests.get(f"{SIGNAL_URL}/v1/receive/{IDENTITY}", timeout=60)
    r.raise_for_status()
    return r.json()


def raw() -> None:
    envs = receive()
    print(f"=== {len(envs)} envelope(s) (RAW -- queue now drained) ===")
    print(json.dumps(envs, indent=2, ensure_ascii=False))


def parse(item: dict) -> dict:
    """Best-effort extraction from a signal-cli envelope. Fields verified/corrected
    against the RAW dump on first run."""
    env = item.get("envelope", item)
    who = env.get("sourceName") or env.get("sourceNumber") or env.get("source") or "?"
    dm = env.get("dataMessage") or {}
    out = {"from": who, "kind": None}
    if dm.get("reaction"):
        rx = dm["reaction"]
        out.update(kind="reaction", emoji=rx.get("emoji"),
                   target_ts=rx.get("targetSentTimestamp"),
                   remove=rx.get("isRemove", False))
    elif dm.get("quote"):
        q = dm["quote"]
        out.update(kind="reply", text=dm.get("message"),
                   target_ts=q.get("id") or q.get("targetSentTimestamp"))
    elif dm.get("message") is not None:
        out.update(kind="message", text=dm.get("message"))
    else:
        out.update(kind="other")
    return out


def watch(muster_ts: int) -> None:
    roster: dict[str, str] = {}   # who -> "in" | "paid"
    print(f"watching muster {muster_ts}; react in Signal (any=join, money=paid). Ctrl-C to stop.\n")
    seen = 0
    while True:
        for item in receive():
            p = parse(item)
            seen += 1
            print(f"  [{p['kind']}] from={p['from']} " +
                  " ".join(f"{k}={v}" for k, v in p.items() if k not in ("kind", "from")))
            if p["kind"] == "reaction" and p.get("target_ts") == muster_ts:
                who = p["from"]
                if p.get("remove"):
                    roster.pop(who, None)
                elif p.get("emoji") in PAID_EMOJI:
                    roster[who] = "paid"
                else:
                    roster.setdefault(who, "in")
                print(f"    -> roster: {roster}")
        time.sleep(3)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "send":
        send(sys.argv[2], sys.argv[3])
    elif cmd == "raw":
        raw()
    elif cmd == "watch":
        watch(int(sys.argv[2]))
    else:
        sys.exit(f"unknown command: {cmd}")
