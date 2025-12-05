# src/sim_runner.py
"""
Simulation runner for MIL-BASTER (updated)

- Initializes DB and keystore (demo mode)
- Creates N nodes with keypairs (if missing)
- Simulates simple routing/forwarding with occasional malicious behavior
- On detection, creates signed+encrypted evidence and persists it
- Runs an anchor worker in background to batch/anchor evidence to chain
- Shows trust updates and simple stats

Run:
    python -m src.sim_runner
"""

import os
import time
import random
import threading
import signal
from typing import List, Dict

# Local imports (make sure these files are present in src/)
from .db_utils import init_db, get_unanchored_evidence
from .crypto_utils import gen_node_keypair, load_node_public_bytes
from .evidence_manager import persist_and_maybe_anchor, start_anchor_loop, anchor_worker_once
from .trust import update_trust
# routing/aodv modules are optional for this demo; we simulate simple forwarding
# from src.aodv_protocol import ...    # not required for this simple sim

# Configuration (can be overridden with env vars)
NUM_NODES = int(os.environ.get("SIM_NUM_NODES", "8"))
SIM_DURATION = int(os.environ.get("SIM_DURATION", "60"))  # seconds
MSG_RATE = float(os.environ.get("SIM_MSG_RATE", "0.5"))   # messages per second per pair
MALICIOUS_RATIO = float(os.environ.get("SIM_MALICIOUS_RATIO", "0.2"))  # fraction of nodes that misbehave
ANCHOR_IN_BACKGROUND = os.environ.get("ANCHOR_BACKGROUND", "1") == "1"

# Simple Node model for the sim
class Node:
    def __init__(self, node_id: str, malicious: bool=False):
        self.node_id = node_id
        self.malicious = malicious
        # trust score is stored in DB by trust.update_trust; local cache for read-only
        self.trust = 100

    def __repr__(self):
        return f"<Node {self.node_id} mal={self.malicious} trust={self.trust}>"

# Global sim state
nodes: List[Node] = []
stop_event = threading.Event()
anchor_thread = None

def setup_keystore_and_nodes(n: int, malicious_ratio: float):
    """
    Ensure each node has a keypair (demo keystore).
    Create Node objects and mark a subset as malicious.
    """
    print(f"[sim] Creating {n} nodes (malicious_ratio={malicious_ratio}) and ensuring keypairs...")
    node_ids = [f"node{idx+1}" for idx in range(n)]
    # generate keypairs if missing
    for nid in node_ids:
        # gen_node_keypair will no-op if keys exist in keystore (per provided crypto_utils)
        gen_node_keypair(nid)
    # pick malicious nodes
    num_mal = max(1, int(n * malicious_ratio))
    mal_set = set(random.sample(node_ids, num_mal))
    global nodes
    nodes = [Node(nid, malicious=(nid in mal_set)) for nid in node_ids]
    print("[sim] Nodes:", nodes)

def pick_path(src_idx: int, dst_idx: int) -> List[int]:
    """
    For simplicity, path is deterministic list of intermediate indices between src and dst.
    In a real sim you'd call AODV route discovery.
    """
    if src_idx == dst_idx:
        return [src_idx]
    if src_idx < dst_idx:
        return list(range(src_idx, dst_idx+1))
    else:
        return list(range(src_idx, dst_idx-1, -1))

def simulate_message(src: Node, dst: Node, msg_id: int):
    """
    Simulate a single message from src -> dst along a simple path.
    If a malicious node on the path drops or tampers, create evidence and update trust.
    """
    src_idx = int(src.node_id.replace("node","")) - 1
    dst_idx = int(dst.node_id.replace("node","")) - 1
    path_indices = pick_path(src_idx, dst_idx)
    path_nodes = [nodes[i] for i in path_indices]

    # Create a payload (small)
    payload = {
        "msg_id": msg_id,
        "src": src.node_id,
        "dst": dst.node_id,
        "ts": int(time.time()),
        "body": f"hello-{msg_id}"
    }

    # Forward step-by-step
    for hop_idx, hop_node in enumerate(path_nodes[1:], start=1):  # skip source (already sent)
        prev_node = path_nodes[hop_idx-1]
        # Decide behavior:
        # - If hop_node is malicious it may drop or tamper (50% each)
        if hop_node.malicious and random.random() < 0.8:  # malicious nodes misbehave with high prob
            action = random.choice(["drop","tamper"])
            evidence_obj = {
                "event": "forward_misbehavior",
                "offender": hop_node.node_id,
                "prev_hop": prev_node.node_id,
                "intended_dst": dst.node_id,
                "msg_payload": payload,
                "action": action,
                "sim_ts": int(time.time())
            }
            # Persist evidence (this will sign+encrypt+save)
            rowid, event_hash = persist_and_maybe_anchor(prev_node.node_id, evidence_obj, peer_pubkey_bytes=None)
            print(f"[sim][EVIDENCE] recorded evidence rowid={rowid} hash={event_hash} for offender={hop_node.node_id} action={action}")

            # Penalize offender's trust
            delta = -20 if action == "drop" else -10
            new_trust = update_trust(hop_node.node_id, delta, prev_score=hop_node.trust)
            hop_node.trust = new_trust
            print(f"[sim][TRUST] Node {hop_node.node_id} penalized ({delta}); new trust={new_trust}")

            # If tamper, simulate modification and continue; if drop, stop forwarding
            if action == "drop":
                print(f"[sim] Message {payload['msg_id']} dropped by {hop_node.node_id}.")
                return False
            else:
                # tamper payload
                payload["body"] = payload["body"] + "-TAMPERED"
                print(f"[sim] Message {payload['msg_id']} tampered by {hop_node.node_id}, continuing.")
                # continue forwarding
        else:
            # benign forwarding: small trust bump
            if not hop_node.malicious:
                new_trust = update_trust(hop_node.node_id, +1, prev_score=hop_node.trust)
                hop_node.trust = new_trust
    # If we reach here, message delivered
    print(f"[sim] Message {payload['msg_id']} delivered from {src.node_id} to {dst.node_id} via {[n.node_id for n in path_nodes]}")
    return True

def run_simulation(duration_seconds: int):
    """
    Main simulation loop: repeatedly pick random src/dst pairs and send messages.
    """
    print(f"[sim] Starting simulation for {duration_seconds} seconds... (press Ctrl-C to stop)")
    end_time = time.time() + duration_seconds
    msg_counter = 0
    try:
        while time.time() < end_time and not stop_event.is_set():
            # pick random src/dst
            src, dst = random.sample(nodes, 2)
            msg_counter += 1
            simulate_message(src, dst, msg_counter)
            # throttle
            time.sleep(1.0 / max(0.001, MSG_RATE))
    except KeyboardInterrupt:
        print("[sim] Interrupted by user.")
    print("[sim] Simulation finished. Sent messages:", msg_counter)
    # final stats
    print("[sim] Final trust scores:")
    for n in nodes:
        print(f"  {n.node_id}: trust={n.trust} malicious={n.malicious}")

def start_anchor_background():
    global anchor_thread
    if ANCHOR_IN_BACKGROUND:
        print("[sim] Starting anchor worker background thread...")
        anchor_thread = threading.Thread(target=start_anchor_loop, kwargs={"loop_forever": True}, daemon=True)
        anchor_thread.start()
    else:
        print("[sim] Anchor background disabled; call anchor_worker_once() manually to anchor batches.")

def signal_handler(sig, frame):
    print("[sim] Signal received, shutting down...")
    stop_event.set()

def main():
    # initialize DB & keystore
    init_db()
    # create nodes and keys
    setup_keystore_and_nodes(NUM_NODES, MALICIOUS_RATIO)
    # start anchor worker background thread if enabled
    start_anchor_background()
    # register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # run simulation
    run_simulation(SIM_DURATION)
    # final anchor flush (attempt to anchor any leftover evidence)
    print("[sim] Running final anchor pass...")
    res = anchor_worker_once()
    print("[sim] Final anchor result:", res)
    print("[sim] Done.")

if __name__ == "__main__":
    main()
