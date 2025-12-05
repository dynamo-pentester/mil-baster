# milbaster_demo.py
"""
Standalone MIL-BASTER demo:
- AODVNode model (based on your models.py)
- SecureMILBASTER simulation (with IsolationForest anomaly detection)
- Matplotlib trust evolution plot
Requires: scikit-learn, matplotlib
Run: python milbaster_demo.py
"""

import asyncio
import random
import math
import time
import json
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Set, Tuple, List, Optional
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import IsolationForest

# ------------------------
# Lightweight crypto_utils stub (replace with your real one)
# ------------------------
def gen_keypair():
    # returns (priv, pub) simple placeholders
    priv = f"priv_{random.getrandbits(64):016x}"
    pub = f"pub_{random.getrandbits(64):016x}"
    return priv, pub

def sha256_hex(b: bytes):
    import hashlib
    return hashlib.sha256(b).hexdigest()

def derive_shared_key(a, b):
    # naive deterministic placeholder
    return (str(a) + str(b)).encode()[:32]

def aes_gcm_encrypt(key: bytes, plaintext: bytes):
    # placeholder: NOT REAL encryption; just return plaintext for demo
    # In production use proper AES-GCM
    return plaintext

def sign_message(priv, msg: bytes):
    return f"sig({priv[:8]})".encode()

# ------------------------
# AODVNode (your models.py adapted)
# ------------------------
@dataclass
class AODVNode:
    node_id: str
    position: Tuple[float, float] = field(default_factory=lambda: (random.uniform(0, 1000), random.uniform(0, 1000)))
    priv: Any = field(default=None)
    pub: Any = field(default=None)
    trust_score: int = 100
    malicious: bool = False

    # AODV Protocol fields
    neighbors: Set[str] = field(default_factory=set)
    routing_table: Dict[str, Dict] = field(default_factory=dict)
    sequence_number: int = field(default_factory=lambda: random.randint(1, 1000))
    rreq_id: int = 0

    # Military fields
    unit_type: str = field(default="INFANTRY") # INFANTRY, ARMOR, AIR, COMMAND
    radio_range: float = field(default=150.0) # meters
    energy_level: float = field(default=100.0) # battery %

    # Statistics
    stats: Dict[str, int] = field(default_factory=lambda: {
        "sent": 0, "forwarded": 0, "dropped": 0,
        "rreq_sent": 0, "rrep_sent": 0, "rerr_sent": 0, "hello_sent": 0,
        "signatures_created": 0, "signatures_verified": 0,
        "messages_sent": 0, "messages_forwarded": 0, "messages_dropped": 0
    })

    # Status
    is_active: bool = True
    pseudonym: str = None
    last_pseudonym_rotation: float = field(default_factory=time.time)
    pseudonym_counter: int = 0

    def __post_init__(self):
        if self.priv is None or self.pub is None:
            p, q = gen_keypair()
            self.priv = p
            self.pub = q

        if self.pseudonym is None:
            self.pseudonym = f"SOLDIER_{self.node_id}"

        range_map = {"INFANTRY": 150, "ARMOR": 200, "AIR": 300, "COMMAND": 250}
        self.radio_range = range_map.get(self.unit_type, 150)
        self.last_pseudonym_rotation = time.time()

    def distance_to(self, other_node: 'AODVNode') -> float:
        dx = self.position[0] - other_node.position[0]
        dy = self.position[1] - other_node.position[1]
        return math.sqrt(dx*dx + dy*dy)

    def can_communicate_with(self, other_node: 'AODVNode') -> bool:
        return self.distance_to(other_node) <= self.radio_range and self.is_active

    def should_rotate_pseudonym(self, interval_minutes: int = 30) -> bool:
        current_time = time.time()
        time_since_last_rotation = current_time - self.last_pseudonym_rotation
        interval_seconds = interval_minutes * 60
        return (
            time_since_last_rotation >= interval_seconds or
            self.trust_score < 40 or
            (self.malicious and random.random() < 0.5)
        )

    def generate_new_pseudonym(self):
        self.pseudonym_counter += 1
        unit_prefixes = {
            "INFANTRY": "GRUNT",
            "ARMOR": "TANK",
            "AIR": "BIRD",
            "COMMAND": "CHIEF"
        }
        prefix = unit_prefixes.get(self.unit_type, "SOLDIER")
        old = self.pseudonym
        self.pseudonym = f"{prefix}_{self.node_id}_{self.pseudonym_counter}"
        self.last_pseudonym_rotation = time.time()
        # Demo print
        print(f"🔄 Node {self.node_id} rotated pseudonym: {old} → {self.pseudonym}")

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "position": self.position,
            "trust_score": self.trust_score,
            "malicious": self.malicious,
            "unit_type": self.unit_type,
            "radio_range": self.radio_range,
            "energy_level": self.energy_level,
            "neighbors": list(self.neighbors),
            "stats": self.stats,
            "is_active": self.is_active,
            "pseudonym": self.pseudonym
        }

def create_100_nodes() -> List[AODVNode]:
    nodes = []
    unit_types = ["INFANTRY"] * 70 + ["ARMOR"] * 20 + ["AIR"] * 5 + ["COMMAND"] * 5
    for i in range(100):
        node = AODVNode(
            node_id=str(i),
            unit_type=unit_types[i],
            position=(
                random.uniform(0, 1000) + random.gauss(0, 50),
                random.uniform(0, 1000) + random.gauss(0, 50)
            )
        )
        nodes.append(node)
    malicious_count = random.randint(8, 9)
    malicious_nodes = random.sample(nodes, malicious_count)
    for node in malicious_nodes:
        node.malicious = True
        node.trust_score = random.randint(50, 75)
        print(f"🚨 THREAT DETECTED: Node {node.node_id} ({node.unit_type}) marked as malicious (trust: {node.trust_score})")
    return nodes

# ------------------------
# Minimal AODVProtocol stub (for demo)
# ------------------------
class AODVProtocol:
    def __init__(self, node: AODVNode):
        self.node = node
    async def send_hello(self, neighbors: List[AODVNode]):
        # Simulate a small delay and update neighbor set
        await asyncio.sleep(0.01)
        self.node.neighbors = set([n.node_id for n in neighbors])
    async def send_rreq(self, dst_id: str, all_nodes: List[AODVNode]):
        await asyncio.sleep(0.01)
        # Return a trivial RREQ "route"
        return [self.node.node_id, dst_id]
    def encrypt_message_for_peer(self, payload_bytes: bytes, dst: AODVNode):
        # Demo encryption placeholder
        return aes_gcm_encrypt(derive_shared_key(self.node.priv, dst.pub), payload_bytes)
    def find_route_to(self, dst_id: str):
        return None
    def find_secure_route_to(self, dst_id: str):
        return None
    def update_secure_routing_table(self, dst_id, next_hop, hop_count, seq, avg_trust):
        return

# ------------------------
# DB utils stubs
# ------------------------
def init_db():
    # demo does nothing
    return
def save_evidence(event_hash, data, ts):
    # write to files for demo
    p = "evidence"
    os.makedirs(p, exist_ok=True)
    open(os.path.join(p, f"{event_hash}.bin"), "wb").write(data)
def save_trust(node_id, trust_value):
    return

# ------------------------
# Trust update helper
# ------------------------
def update_trust(node: AODVNode, delta: int, reason: str = "") -> int:
    before = node.trust_score
    node.trust_score = max(0, min(100, node.trust_score + delta))
    save_trust(node.node_id, node.trust_score)
    return node.trust_score

# ------------------------
# SlidingWindowMonitor with IsolationForest
# ------------------------
class SlidingWindowMonitor:
    def __init__(self, window_msgs=30, window_seconds=60, contamination=0.05):
        self.window_msgs = window_msgs
        self.window_seconds = window_seconds
        self.feature_history: Dict[str, List[List[float]]] = {}
        self.event_history: Dict[str, List[Dict]] = {}
        self.model = IsolationForest(contamination=contamination, random_state=42)
        # A record of drop rates for simple anomaly metric
        self.drop_rates: Dict[str, float] = {}

    def record(self, node_id: str, forwarded: bool):
        # store event
        now = time.time()
        if node_id not in self.event_history:
            self.event_history[node_id] = []
        self.event_history[node_id].append({"t": now, "forwarded": forwarded})
        # trim by time
        self.event_history[node_id] = [e for e in self.event_history[node_id] if now - e["t"] <= self.window_seconds]
        # update drop rate
        evs = self.event_history[node_id]
        drops = sum(1 for e in evs if not e["forwarded"])
        self.drop_rates[node_id] = drops / max(1, len(evs))

    def extract_features(self, node: AODVNode):
        # features inspired by your model: normalized trust, energy, messages sent/dropped, signatures_verified
        msgs_sent = node.stats.get("messages_sent", 0)
        msgs_dropped = node.stats.get("messages_dropped", 0)
        sigs_verified = node.stats.get("signatures_verified", 0)
        drop_rate = self.drop_rates.get(node.node_id, 0.0)
        return [
            node.trust_score / 100.0,
            node.energy_level / 100.0,
            np.tanh(msgs_sent / 50.0),
            np.tanh(msgs_dropped / 10.0),
            np.tanh(sigs_verified / 10.0),
            drop_rate
        ]

    def add_node_features(self, node: AODVNode):
        feats = self.extract_features(node)
        if node.node_id not in self.feature_history:
            self.feature_history[node.node_id] = []
        self.feature_history[node.node_id].append(feats)
        if len(self.feature_history[node.node_id]) > self.window_msgs:
            self.feature_history[node.node_id].pop(0)

    def train_and_detect(self, nodes: List[AODVNode]):
        # gather all recent features
        all_feats = []
        node_map = []
        for nid, feats_list in self.feature_history.items():
            for f in feats_list:
                all_feats.append(f)
                node_map.append(nid)
        if len(all_feats) < max(30, len(nodes)):  # require some amount of data to train
            return set()
        X = np.array(all_feats)
        try:
            self.model.fit(X)
            preds = self.model.predict(X)  # 1 normal, -1 anomaly
        except Exception as e:
            # fallback: no detection
            print(f"⚠️ IsolationForest error: {e}")
            return set()

        anomalies = set()
        for i, nid in enumerate(node_map):
            if preds[i] == -1:
                anomalies.add(nid)
        return anomalies

    def is_anomalous(self, node_id: str):
        # simple accessor
        dr = self.drop_rates.get(node_id, 0.0)
        return (dr > 0.5), dr

# ------------------------
# SecureMILBASTER (main sim class)
# ------------------------
MSG_RATE_PER_NODE = 0.05  # seconds for fast demo
MALICIOUS_DROP_RATE = 0.7
TRUST_DECREMENT = -15
TRUST_INCREMENT = 1
EXCLUDE_THRESHOLD = 40

class SecureMILBASTER:
    def __init__(self):
        self.nodes: List[AODVNode] = []
        self.protocols: Dict[str, AODVProtocol] = {}
        self.anomaly_monitor = SlidingWindowMonitor(window_msgs=40, window_seconds=30, contamination=0.07)
        self.simulation_state = {
            "running": False,
            "total_messages": 0,
            "successful_deliveries": 0,
            "anomalies_detected": 0,
            "blockchain_events": 0,
            "pseudonym_rotations": 0,
            "trust_violations": 0
        }
        self.security_metrics = {
            "encryption_operations": 0,
            "signature_verifications": 0,
            "replay_attempts_blocked": 0,
            "low_trust_nodes_excluded": 0
        }
        # history for plotting
        self.trust_history: Dict[str, List[int]] = {}

    def initialize_network(self):
        init_db()
        self.nodes = create_100_nodes()
        for node in self.nodes:
            self.protocols[node.node_id] = AODVProtocol(node)
            self.trust_history[node.node_id] = [node.trust_score]
        self.update_network_topology()

    def update_network_topology(self):
        for node in self.nodes:
            if not node.is_active:
                continue
            # determine neighbors within radio range and with trust >= EXCLUDE_THRESHOLD (allow malicious in neighbor list for detection)
            trusted_neighbors = [other for other in self.nodes if node.can_communicate_with(other)]
            asyncio.create_task(self.protocols[node.node_id].send_hello(trusted_neighbors))

    def get_node_by_id(self, node_id: str) -> Optional[AODVNode]:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None

    async def secure_route_discovery(self, src: AODVNode, dst: AODVNode):
        src_protocol = self.protocols[src.node_id]
        cached = src_protocol.find_secure_route_to(dst.node_id) or src_protocol.find_route_to(dst.node_id)
        if cached:
            route_node_ids = cached
            route_nodes = [self.get_node_by_id(nid) for nid in route_node_ids]
            return [n for n in route_nodes if n]
        # build simple route: src -> some intermediates -> dst
        intermediates = [n for n in self.nodes if n.node_id not in (src.node_id, dst.node_id) and n.is_active]
        if intermediates:
            sampled = random.sample(intermediates, k=min(2, len(intermediates)))
            return [src] + sampled + [dst]
        return [src, dst]

    async def send_encrypted_message(self, src: AODVNode, dst: AODVNode) -> bool:
        route = await self.secure_route_discovery(src, dst)
        if len(route) < 2:
            return False
        payload = {
            "from": src.pseudonym,
            "to": dst.pseudonym,
            "message": f"TACTICAL_MSG_{int(time.time())}",
            "timestamp": time.time(),
            "nonce": random.randint(1000000, 9999999)
        }
        payload_bytes = json.dumps(payload).encode()
        # encrypt using protocol
        protocol = self.protocols[src.node_id]
        encrypted_payload = protocol.encrypt_message_for_peer(payload_bytes, dst)
        self.security_metrics["encryption_operations"] += 1

        # forward through route (simulate drops)
        for hop in route[1:]:
            # anomaly monitor record
            if hop.malicious and random.random() < MALICIOUS_DROP_RATE:
                self.anomaly_monitor.record(hop.node_id, forwarded=False)
                await self.handle_security_incident(hop, route, payload, "packet_drop")
                return False
            else:
                self.anomaly_monitor.record(hop.node_id, forwarded=True)
                hop.stats["forwarded"] += 1
                update_trust(hop, TRUST_INCREMENT, "successful_forward")

        self.simulation_state["successful_deliveries"] += 1
        src.stats["sent"] += 1
        return True

    async def handle_security_incident(self, malicious_node: AODVNode, route: List[AODVNode], payload: Dict, incident_type: str):
        malicious_node.stats["dropped"] += 1
        self.simulation_state["anomalies_detected"] += 1
        self.simulation_state["trust_violations"] += 1

        evidence = {
            "event": incident_type,
            "malicious_node": malicious_node.node_id,
            "route": [n.node_id for n in route],
            "payload_hash": sha256_hex(json.dumps(payload).encode()),
            "timestamp": time.time(),
            "position": malicious_node.position,
            "unit_type": malicious_node.unit_type,
            "trust_score_before": malicious_node.trust_score,
            "pseudonym": malicious_node.pseudonym
        }
        ev_bytes = json.dumps(evidence).encode()
        enc_ev = aes_gcm_encrypt(b"demo_key_32_bytes_for_evidence_enc", ev_bytes)
        ev_hash = sha256_hex(enc_ev)
        save_evidence(ev_hash, enc_ev, int(time.time()))
        new_trust = update_trust(malicious_node, TRUST_DECREMENT, f"{incident_type}_detected")
        malicious_node.generate_new_pseudonym()
        self.simulation_state["pseudonym_rotations"] += 1
        print(f"🚨 SECURITY INCIDENT: Node {malicious_node.node_id} {incident_type}. Trust→{new_trust}")

    async def periodic_security_maintenance(self):
        while self.simulation_state["running"]:
            for node in self.nodes:
                if node.should_rotate_pseudonym(interval_minutes=30):
                    node.generate_new_pseudonym()
                    self.simulation_state["pseudonym_rotations"] += 1

            # Build features, run ML detection
            for node in self.nodes:
                # simulate some message generation
                inc_sent = random.randint(0, 3)
                node.stats["messages_sent"] += inc_sent
                if node.malicious:
                    node.stats["messages_dropped"] += random.randint(0, 2)
                # sample energy drain
                node.energy_level = max(0.0, node.energy_level - random.uniform(0.0, 0.5))

                self.anomaly_monitor.add_node_features(node)

            anomalies = self.anomaly_monitor.train_and_detect(self.nodes)
            for nid in anomalies:
                node = self.get_node_by_id(nid)
                if node and not node.malicious:
                    # penalize honest-looking anomalous nodes
                    update_trust(node, TRUST_DECREMENT, "ml_anomaly_detected")
                    self.simulation_state["anomalies_detected"] += 1
                    node.generate_new_pseudonym()
                    self.simulation_state["pseudonym_rotations"] += 1

            # update trust history
            for node in self.nodes:
                self.trust_history[node.node_id].append(node.trust_score)

            # topology recalculation
            self.update_network_topology()
            await asyncio.sleep(1.0)

    async def node_communication_loop(self, node: AODVNode):
        while self.simulation_state["running"]:
            if not node.is_active or node.trust_score < EXCLUDE_THRESHOLD:
                await asyncio.sleep(MSG_RATE_PER_NODE)
                continue
            potential_destinations = [n for n in self.nodes if n.node_id != node.node_id and n.is_active and n.trust_score >= EXCLUDE_THRESHOLD]
            if potential_destinations:
                dst = random.choice(potential_destinations)
                success = await self.send_encrypted_message(node, dst)
                self.simulation_state["total_messages"] += 1
            await asyncio.sleep(MSG_RATE_PER_NODE)

    async def run_secure_simulation(self, duration_seconds: int = 60):
        print(f"🚀 Starting simulation for {duration_seconds} seconds...")
        self.simulation_state["running"] = True
        # node tasks
        node_tasks = [asyncio.create_task(self.node_communication_loop(n)) for n in self.nodes]
        maintenance_task = asyncio.create_task(self.periodic_security_maintenance())
        all_tasks = node_tasks + [maintenance_task]
        try:
            await asyncio.wait_for(asyncio.gather(*all_tasks, return_exceptions=True), timeout=duration_seconds)
        except asyncio.TimeoutError:
            print("✅ Simulation duration reached.")
        finally:
            self.simulation_state["running"] = False

    def get_comprehensive_stats(self):
        total_nodes = len(self.nodes)
        active_nodes = len([n for n in self.nodes if n.is_active])
        malicious_nodes = len([n for n in self.nodes if n.malicious])
        low_trust_nodes = len([n for n in self.nodes if n.trust_score < EXCLUDE_THRESHOLD])
        avg_trust = sum(n.trust_score for n in self.nodes) / total_nodes if total_nodes else 0
        return {
            **self.simulation_state,
            **self.security_metrics,
            "total_nodes": total_nodes,
            "active_nodes": active_nodes,
            "malicious_nodes": malicious_nodes,
            "low_trust_nodes": low_trust_nodes,
            "average_trust": avg_trust
        }

# ------------------------
# Runner & plotting
# ------------------------
async def main_demo():
    sim = SecureMILBASTER()
    sim.initialize_network()
    # run for 30 seconds demo
    await sim.run_secure_simulation(duration_seconds=30)

    stats = sim.get_comprehensive_stats()
    print("\nFINAL STATS:", stats)

    # Plot trust evolution for first 20 nodes
    node_ids = [str(i) for i in range(20)]
    plt.figure(figsize=(12, 6))
    for nid in node_ids:
        history = sim.trust_history.get(nid, [])
        plt.plot(history, label=f"Node {nid}", linewidth=1)
    plt.title("Trust Evolution (first 20 nodes)")
    plt.xlabel("Simulation ticks")
    plt.ylabel("Trust Score")
    plt.ylim(0, 100)
    plt.grid(alpha=0.3)
    plt.legend(ncol=2, fontsize="small")
    plt.tight_layout()
    plt.show()

    # Plot average trust over time
    avg = []
    max_len = max(len(v) for v in sim.trust_history.values())
    for t in range(max_len):
        vals = []
        for v in sim.trust_history.values():
            if t < len(v):
                vals.append(v[t])
        if vals:
            avg.append(sum(vals) / len(vals))
    plt.figure(figsize=(8,4))
    plt.plot(avg, linewidth=2)
    plt.title("Average Trust Over Time")
    plt.xlabel("Simulation ticks")
    plt.ylabel("Average Trust")
    plt.ylim(0, 100)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    try:
        asyncio.run(main_demo())
    except KeyboardInterrupt:
        print("Stopped by user")
