#!/usr/bin/env python3
"""
DNS Beaconing - Simulates C2 communication via periodic DNS queries
"""

import json
import random
import signal
import socket
import sys
import time
from multiprocessing import Event, Process, Value

import dns.resolver
import dns.exception

if len(sys.argv) != 5:
    print(f"Usage: {sys.argv[0]} <RESOLVER_IP> <INTERVAL_S> <JITTER_FRAC> <LABEL_LEN>")
    sys.exit(1)

RESOLVER_IP = sys.argv[1]
INTERVAL_S = float(sys.argv[2])
JITTER_FRAC = float(sys.argv[3])
LABEL_LEN = int(sys.argv[4])

BASE_DOMAINS = ["lab.local", "iot.local"]
QTYPES = ["A", "AAAA", "TXT"]
NUM_WORKERS = 1
DNS_TIMEOUT_S = 2.0
RNG_SEED = 20260111

def jittered_interval(rng: random.Random, base: float, frac: float) -> float:
    if frac <= 0:
        return max(0.1, base)
    return max(0.1, base * rng.uniform(1.0 - frac, 1.0 + frac))

def make_resolver() -> dns.resolver.Resolver:
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = [RESOLVER_IP]
    r.timeout = DNS_TIMEOUT_S
    r.lifetime = DNS_TIMEOUT_S
    r.retry_servfail = False
    return r

def high_entropy_label(rng: random.Random, n: int) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    n = max(1, min(63, n))
    return "".join(rng.choice(alphabet) for _ in range(n))

def dns_worker(idx: int,
               stop_event: Event,
               sent: Value,
               ok: Value,
               nxd: Value,
               tout: Value,
               other: Value,
               seed_base: int) -> None:

    rng = random.Random(seed_base + idx)
    resolver = make_resolver()

    while not stop_event.is_set():
        label = high_entropy_label(rng, LABEL_LEN)
        qname = f"{label}.{rng.choice(BASE_DOMAINS)}"
        qtype = rng.choice(QTYPES)

        t0 = time.time()
        try:
            _ = resolver.resolve(qname, qtype, raise_on_no_answer=False, lifetime=DNS_TIMEOUT_S)
            with ok.get_lock():
                ok.value += 1
        except dns.resolver.NXDOMAIN:
            with nxd.get_lock():
                nxd.value += 1
        except dns.resolver.Timeout:
            with tout.get_lock():
                tout.value += 1
        except dns.exception.DNSException:
            with other.get_lock():
                other.value += 1

        with sent.get_lock():
            sent.value += 1

        sleep_s = jittered_interval(rng, INTERVAL_S, JITTER_FRAC) - (time.time() - t0)
        if sleep_s > 0:
            time.sleep(sleep_s)

def main() -> int:
    attack_id = f"DNS_BEACON_{int(time.time())}_{random.randint(1000,9999)}"
    start_ts = time.time()

    sent = Value("i", 0)
    ok = Value("i", 0)
    nxd = Value("i", 0)
    tout = Value("i", 0)
    other = Value("i", 0)
    stop_event = Event()

    print("=" * 60)
    print(f"DNS Beaconing Attack")
    print(f"Attack ID: {attack_id}")
    print(f"Resolver: {RESOLVER_IP}")
    print(f"Interval: {INTERVAL_S}s (jitter: ±{JITTER_FRAC*100:.0f}%)")
    print(f"Label length: {LABEL_LEN} chars")
    print(f"Query types: {QTYPES}")
    print(f"Base domains: {BASE_DOMAINS}")
    print(f"Mode: CONTINUOUS (Press Ctrl+C to stop)")
    print("=" * 60)

    procs = []
    for i in range(NUM_WORKERS):
        p = Process(
            target=dns_worker,
            args=(i, stop_event, sent, ok, nxd, tout, other, RNG_SEED),
            daemon=True
        )
        p.start()
        procs.append(p)

    interrupted = False

    def _handle_sig(_sig, _frame):
        nonlocal interrupted
        interrupted = True
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_sig)
    signal.signal(signal.SIGTERM, _handle_sig)

    try:
        while not stop_event.is_set():
            time.sleep(1.0)
            if sent.value > 0 and sent.value % 100 == 0:
                print(f"[dns_beaconing] Sent {sent.value} queries...")
    finally:
        stop_event.set()
        time.sleep(0.5)
        for p in procs:
            if p.is_alive():
                p.join(timeout=2.0)

    end_ts = time.time()
    duration = round(end_ts - start_ts, 3)

    print(f"\n[dns_beaconing] Stopped by user")
    print(f"[dns_beaconing] Duration: {duration}s")
    print(f"[dns_beaconing] Total queries: {sent.value}")
    print(f"[dns_beaconing] OK: {ok.value}, NXDOMAIN: {nxd.value}, Timeout: {tout.value}, Other: {other.value}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
