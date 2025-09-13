# sim_runner.py
# Main simulation runner: creates nodes, simulates messages, anomalies, trust changes,
# stores encrypted evidence and event_hash. No real Web3 calls here (placeholder provided).

import asyncio
import time
import json
import random
from models import Node
from routing import choose_route
from anomaly import SlidingWindowMonitor
from trust import update_trust
from db_utils import init_db, save_evidence
from crypto_utils import sign_message, verify_signature, sha256_hex, aes_gcm_encrypt, derive_shared_key, b64
from onion import build_onion
from typing import List

# Demo parameters
MSG_RATE_PER_NODE = 1.0  # seconds per message
WINDOW_MSGS = 20
WINDOW_SECONDS = 30
DROP_THRESHOLD = 0.3
TRUST_DECREMENT = -20
TRUST_INCREMENT = 1
EXCLUDE_THRESHOLD = 50

monitor = SlidingWindowMonitor(window_msgs=WINDOW_MSGS, window_seconds=WINDOW_SECONDS)

def make_nodes(n=6):
    nodes = []
    for i in range(n):
        nd = Node(node_id=str(i))
        nodes.append(nd)
    # mark one node malicious for demo
    malicious = random.choice(nodes)
    malicious.malicious = True
    print("Malicious node:", malicious.node_id)
    return nodes

async def send_message(nodes: List[Node], src: Node, dst: Node, route: List[Node]):
    # payload
    payload = {"from": src.pseudonym, "to": dst.pseudonym, "body": f"hello_{int(time.time())}"}
    payload_b = json.dumps(payload).encode()
    # build onion using pub keys of intermediate nodes (skip src/dst)
    hop_pubs = [n.pub for n in route[1:-1]]  # intermediates
    onion = build_onion(payload_b, hop_pubs, src.priv) if hop_pubs else payload_b
    # sign the top-level onion
    sig = sign_message(src.priv, onion)
    # forward hop by hop
    for hop in route[1:]:
        # if hop is malicious, simulate drop/delay/alter
        if hop.malicious and random.random() < 0.6:
            # drop
            monitor.record_forward(hop.node_id, False)
            hop.stats["dropped"] += 1
            # create evidence, push local, adjust trust
            evidence = json.dumps({
                "event":"drop",
                "hop":hop.node_id,
                "route":[p.node_id for p in route],
                "ts":int(time.time())
            }).encode()
            # encrypt evidence with a local ephemeral key (demo uses src-derived key)
            # derive key between src and hop for demo encryption; in real world use device/gateway key
            sk = derive_shared_key(src.priv, hop.pub)
            encrypted = aes_gcm_encrypt(sk, evidence)
            event_hash = sha256_hex(encrypted)
            save_evidence(event_hash, encrypted, int(time.time()))
            # update trust
            new_trust = update_trust(hop, TRUST_DECREMENT, "drop_detected")
            print(f"[ANOMALY] Node {hop.node_id} dropped packet. trust -> {new_trust}. event_hash={event_hash[:12]}...")
            # record anomaly into monitor (already done)
            # Do not forward further
            return False
        else:
            # forwarded
            monitor.record_forward(hop.node_id, True)
            hop.stats["forwarded"] += 1
            # hop peels layer if needed (not fully decoding in demo)
            await asyncio.sleep(0.01)
    # success -> increment trust on all hops
    for n in route:
        update_trust(n, TRUST_INCREMENT, "successful_forward")
    return True

async def node_loop(nodes: List[Node], node: Node):
    while True:
        # randomly select a destination different from node
        dst = random.choice([n for n in nodes if n.node_id != node.node_id])
        route = choose_route(nodes, node, dst, hops=2, exclude_below=EXCLUDE_THRESHOLD)
        # send
        ok = await send_message(nodes, node, dst, route)
        node.stats["sent"] += 1
        await asyncio.sleep(MSG_RATE_PER_NODE)

async def main():
    init_db()
    nodes = make_nodes(6)
    tasks = []
    for n in nodes:
        tasks.append(asyncio.create_task(node_loop(nodes, n)))
    # Also monitor sliding window and apply trust drops when threshold crossed
    async def monitor_loop():
        while True:
            for n in nodes:
                anomalous, rate = monitor.is_anomalous(n.node_id, drop_threshold=DROP_THRESHOLD)
                if anomalous:
                    # penalize if not already low
                    if n.trust_score > EXCLUDE_THRESHOLD:
                        update_trust(n, TRUST_DECREMENT, f"auto_penalty_drop_rate_{rate:.2f}")
                        print(f"[AUTO] Node {n.node_id} auto-penalized. drop_rate={rate:.2f} trust={n.trust_score}")
            await asyncio.sleep(5)
    tasks.append(asyncio.create_task(monitor_loop()))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Simulation stopped.")
