# src/sim_runner_fixed.py
# Enhanced 100-node AODV simulation with comprehensive security features

import asyncio
import time
import json
import random
import os
from typing import List, Dict, Optional

# Import fixed modules (adjust imports based on your file structure)
from .models import AODVNode, create_100_nodes
from .aodv_protocol import AODVProtocol, RouteRequest, RouteReply
from .crypto_utils import sign_message, aes_gcm_encrypt, derive_shared_key, sha256_hex
from .db_utils import init_db, save_evidence, save_trust
from .trust import update_trust
from .monitoring import SlidingWindowMonitor

# Try to import blockchain utils with fallback
try:
    from .web3_utils import push_event_to_chain, get_blockchain_status
    BLOCKCHAIN_AVAILABLE = True
except ImportError:
    print("⚠️ Blockchain utilities not available - running in offline mode")
    BLOCKCHAIN_AVAILABLE = False
    def push_event_to_chain(*args, **kwargs):
        return None
    def get_blockchain_status():
        return {"connected": False, "offline_mode": True}

# Enhanced simulation parameters
MSG_RATE_PER_NODE = 2.0  # Increased to reduce RPC load
MALICIOUS_DROP_RATE = 0.7
TRUST_DECREMENT = -15
TRUST_INCREMENT = 1
EXCLUDE_THRESHOLD = 40
HELLO_INTERVAL = 5.0
PSEUDONYM_ROTATION_INTERVAL = 1800  # 30 minutes

class SecureMILBASTER:
    """Enhanced MIL-BASTER simulation with comprehensive security features"""

    def __init__(self):
        self.nodes: List[AODVNode] = []
        self.protocols: Dict[str, AODVProtocol] = {}
        self.anomaly_monitor = SlidingWindowMonitor(window_msgs=30, window_seconds=60)

        self.simulation_state = {
            "running": False,
            "total_messages": 0,
            "successful_deliveries": 0,
            "anomalies_detected": 0,
            "blockchain_events": 0,
            "network_connectivity": 0.0,
            "pseudonym_rotations": 0,
            "trust_violations": 0
        }

        # Security metrics
        self.security_metrics = {
            "encryption_operations": 0,
            "signature_verifications": 0,
            "replay_attempts_blocked": 0,
            "low_trust_nodes_excluded": 0
        }

    def initialize_network(self):
        """Initialize secure 100-node military network"""
        print("🏗️ Initializing secure 100-node military MANET...")
        print(f"🔐 Security Features: Pseudonyms, Trust-based routing, End-to-end encryption")

        # Initialize database
        init_db()

        # Check blockchain status
        if BLOCKCHAIN_AVAILABLE:
            blockchain_status = get_blockchain_status()
            if blockchain_status.get("connected"):
                print(f"⛓️ Blockchain connected: {blockchain_status.get('current_rpc', 'Unknown')[:50]}...")
            else:
                print("⚠️ Blockchain offline - using local evidence storage only")

        # Create 100 soldier nodes with enhanced security
        self.nodes = create_100_nodes()

        # Initialize secure AODV protocols
        for node in self.nodes:
            # Use SecureAODVProtocol if available, fallback to basic
            try:
                from .aodv_protocol import SecureAODVProtocol
                self.protocols[node.node_id] = SecureAODVProtocol(node)
            except ImportError:
                self.protocols[node.node_id] = AODVProtocol(node)

        # Calculate initial network topology
        self.update_network_topology()

        print(f"✅ Secure network initialized: {len(self.nodes)} soldiers deployed")
        print(f" • Infantry: {len([n for n in self.nodes if n.unit_type == 'INFANTRY'])}")
        print(f" • Armor: {len([n for n in self.nodes if n.unit_type == 'ARMOR'])}")
        print(f" • Air Support: {len([n for n in self.nodes if n.unit_type == 'AIR'])}")
        print(f" • Command: {len([n for n in self.nodes if n.unit_type == 'COMMAND'])}")
        print(f" • Malicious: {len([n for n in self.nodes if n.malicious])}")

    def update_network_topology(self):
        """Update neighbor relationships with trust-based filtering"""
        for node in self.nodes:
            if not node.is_active:
                continue

            trusted_neighbors = []
            for other_node in self.nodes:
                if (node.can_communicate_with(other_node) and 
                    other_node.trust_score >= EXCLUDE_THRESHOLD and
                    not other_node.malicious):
                    trusted_neighbors.append(other_node)

            # Update protocol neighbors (async task)
            protocol = self.protocols[node.node_id]
            asyncio.create_task(protocol.send_hello(trusted_neighbors))

    async def secure_route_discovery(self, src: AODVNode, dst: AODVNode) -> List[AODVNode]:
        """Enhanced AODV route discovery with trust filtering"""
        src_protocol = self.protocols[src.node_id]

        # Check for cached secure route
        cached_route = None
        if hasattr(src_protocol, 'find_secure_route_to'):
            cached_route = src_protocol.find_secure_route_to(dst.node_id)
        else:
            cached_route = src_protocol.find_route_to(dst.node_id)

        if cached_route:
            route_nodes = [self.get_node_by_id(node_id) for node_id in cached_route]
            trusted_route = [node for node in route_nodes if node and node.trust_score >= EXCLUDE_THRESHOLD]
            if len(trusted_route) >= 2:  # At least src and dst
                return trusted_route

        # Send RREQ for route discovery
        rreq = await src_protocol.send_rreq(dst.node_id, self.nodes)

        # Filter intermediate nodes by trust (allow malicious for detection)
        intermediate_nodes = [
            node for node in self.nodes
            if (node.node_id not in (src.node_id, dst.node_id) and
                node.trust_score >= EXCLUDE_THRESHOLD and
                node.is_active)
        ]

        if intermediate_nodes:
            # Select 2-3 trusted intermediate nodes
            num_hops = min(3, len(intermediate_nodes))
            selected_intermediates = random.sample(intermediate_nodes, num_hops)
            route = [src] + selected_intermediates + [dst]
        else:
            # Direct route if no trusted intermediates
            route = [src, dst]

        # Update routing table with trust information
        if hasattr(src_protocol, 'update_secure_routing_table'):
            avg_trust = sum(node.trust_score for node in route) // len(route)
            src_protocol.update_secure_routing_table(
                dst.node_id, route[1].node_id if len(route) > 1 else dst.node_id,
                len(route) - 1, dst.sequence_number, avg_trust
            )

        return route

    async def send_encrypted_message(self, src: AODVNode, dst: AODVNode) -> bool:
        """Send encrypted message with comprehensive security"""
        # Discover secure route
        route = await self.secure_route_discovery(src, dst)
        if len(route) < 2:
            return False

        # Create message payload with pseudonyms
        payload = {
            "from": src.pseudonym,
            "to": dst.pseudonym,
            "message": f"TACTICAL_MSG_{int(time.time())}",
            "priority": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "timestamp": time.time(),
            "nonce": random.randint(1000000, 9999999)  # Prevent replay
        }

        # Encrypt payload with destination's public key
        payload_bytes = json.dumps(payload).encode()

        # Use session key encryption if available
        protocol = self.protocols[src.node_id]
        if hasattr(protocol, 'encrypt_message_for_peer'):
            encrypted_payload = protocol.encrypt_message_for_peer(payload_bytes, dst)
            self.security_metrics["encryption_operations"] += 1
        else:
            # Fallback to basic encryption
            session_key = derive_shared_key(src.priv, dst.pub)
            encrypted_payload = aes_gcm_encrypt(session_key, payload_bytes)
            self.security_metrics["encryption_operations"] += 1

        # Simulate message forwarding through secure route
        for i, hop in enumerate(route[1:], 1):  # Skip source
            # Record forwarding attempt for anomaly detection
            if hop.malicious and random.random() < MALICIOUS_DROP_RATE:
                # Malicious node drops packet
                self.anomaly_monitor.record(hop.node_id, forwarded=False)
                await self.handle_security_incident(hop, route, payload, "packet_drop")
                return False
            else:
                # Successful forwarding
                self.anomaly_monitor.record(hop.node_id, forwarded=True)
                hop.stats["forwarded"] += 1
                update_trust(hop, TRUST_INCREMENT, "successful_forward")

        # Message delivered successfully
        self.simulation_state["successful_deliveries"] += 1
        src.stats["sent"] += 1
        return True

    async def handle_security_incident(self, malicious_node: AODVNode, route: List[AODVNode], 
                                     payload: Dict, incident_type: str):
        """Handle security incidents with comprehensive logging"""
        malicious_node.stats["dropped"] += 1
        self.simulation_state["anomalies_detected"] += 1
        self.simulation_state["trust_violations"] += 1

        # Create detailed evidence
        evidence = {
            "event": incident_type,
            "malicious_node": malicious_node.node_id,
            "route": [node.node_id for node in route],
            "payload_hash": sha256_hex(json.dumps(payload).encode()),
            "timestamp": time.time(),
            "position": malicious_node.position,
            "unit_type": malicious_node.unit_type,
            "trust_score_before": malicious_node.trust_score,
            "pseudonym": malicious_node.pseudonym
        }

        # Encrypt and store evidence locally
        evidence_bytes = json.dumps(evidence).encode()
        encryption_key = b"demo_key_32_bytes_for_evidence_enc"  # Use proper key derivation in production
        encrypted_evidence = aes_gcm_encrypt(encryption_key, evidence_bytes)
        event_hash = sha256_hex(encrypted_evidence)

        # Save to local database
        save_evidence(event_hash, encrypted_evidence, int(time.time()))

        # Update trust score
        new_trust = update_trust(malicious_node, TRUST_DECREMENT, f"{incident_type}_detected")

        # Try to push to blockchain (with error handling)
        blockchain_success = False
        if BLOCKCHAIN_AVAILABLE:
            try:
                tx_hash = push_event_to_chain(event_hash, 1, TRUST_DECREMENT)
                if tx_hash:
                    blockchain_success = True
                    self.simulation_state["blockchain_events"] += 1
                    print(f"⛓️ Evidence logged to blockchain: {tx_hash[:16]}...")
            except Exception as e:
                print(f"⚠️ Blockchain logging failed (continuing with local storage): {str(e)[:50]}...")

        # Force pseudonym rotation for compromised node
        malicious_node.generate_new_pseudonym()
        self.simulation_state["pseudonym_rotations"] += 1

        print(f"🚨 SECURITY INCIDENT: {malicious_node.unit_type} {malicious_node.node_id} "
              f"{incident_type}. Trust: {malicious_node.trust_score}→{new_trust}. "
              f"Hash: {event_hash[:12]}... {'⛓️' if blockchain_success else '💾'}")

    async def periodic_security_maintenance(self):
        """Periodic security maintenance tasks"""
        while self.simulation_state["running"]:
            current_time = time.time()

            # Rotate pseudonyms periodically
            for node in self.nodes:
                if node.should_rotate_pseudonym(interval_minutes=30):
                    node.generate_new_pseudonym()
                    self.simulation_state["pseudonym_rotations"] += 1

            # Check for anomalous nodes
            for node in self.nodes:
                if not node.malicious:  # Don't check known malicious nodes
                    is_anomalous, drop_rate = self.anomaly_monitor.is_anomalous(node.node_id)
                    if is_anomalous:
                        print(f"🔍 Anomaly detected: Node {node.node_id} drop rate: {drop_rate:.2%}")
                        await self.handle_security_incident(
                            node, [node], {}, "anomalous_behavior"
                        )

            # Update network topology with trust filtering
            self.update_network_topology()

            # Randomly reassign some malicious nodes (simulate changing threats)
            if random.random() < 0.03:  # 3% chance per maintenance cycle
                await self.reassign_threats()

            await asyncio.sleep(15.0)  # Every 15 seconds

    async def reassign_threats(self):
        """Randomly reassign malicious nodes to simulate dynamic threats"""
        # Clear some current malicious status
        current_malicious = [n for n in self.nodes if n.malicious]
        if current_malicious:
            nodes_to_clear = random.sample(current_malicious, random.randint(1, 3))
            for node in nodes_to_clear:
                node.malicious = False
                node.trust_score = min(100, node.trust_score + 20)  # Partial trust restoration

        # Assign new malicious nodes
        honest_nodes = [n for n in self.nodes if not n.malicious and n.trust_score > 60]
        if honest_nodes:
            new_malicious_count = random.randint(1, 3)
            new_malicious = random.sample(honest_nodes, min(new_malicious_count, len(honest_nodes)))
            for node in new_malicious:
                node.malicious = True
                print(f"⚠️ NEW THREAT: Node {node.node_id} ({node.unit_type}) compromised")

    def get_node_by_id(self, node_id: str) -> Optional[AODVNode]:
        """Get node by ID"""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive network and security statistics"""
        total_nodes = len(self.nodes)
        active_nodes = len([n for n in self.nodes if n.is_active])
        malicious_nodes = len([n for n in self.nodes if n.malicious])
        low_trust_nodes = len([n for n in self.nodes if n.trust_score < EXCLUDE_THRESHOLD])
        avg_trust = sum(n.trust_score for n in self.nodes) / total_nodes if total_nodes > 0 else 0

        return {
            **self.simulation_state,
            **self.security_metrics,
            "total_nodes": total_nodes,
            "active_nodes": active_nodes,
            "malicious_nodes": malicious_nodes,
            "low_trust_nodes": low_trust_nodes,
            "average_trust": avg_trust,
            "network_connectivity": self.calculate_connectivity(),
            "blockchain_status": get_blockchain_status() if BLOCKCHAIN_AVAILABLE else {"offline": True}
        }

    def calculate_connectivity(self) -> float:
        """Calculate network connectivity percentage (trust-filtered)"""
        if not self.nodes:
            return 0.0

        trusted_nodes = [n for n in self.nodes if n.trust_score >= EXCLUDE_THRESHOLD and n.is_active]
        if len(trusted_nodes) < 2:
            return 0.0

        total_possible = len(trusted_nodes) * (len(trusted_nodes) - 1) // 2
        actual_connections = 0

        for i, node1 in enumerate(trusted_nodes):
            for node2 in trusted_nodes[i+1:]:
                if node1.can_communicate_with(node2):
                    actual_connections += 1

        return (actual_connections / total_possible) * 100 if total_possible > 0 else 0.0

    async def node_communication_loop(self, node: AODVNode):
        """Individual node secure communication loop"""
        while self.simulation_state["running"]:
            if not node.is_active or node.trust_score < EXCLUDE_THRESHOLD:
                await asyncio.sleep(MSG_RATE_PER_NODE)
                continue

            # Select random trusted destination
            potential_destinations = [
                n for n in self.nodes
                if (n.node_id != node.node_id and 
                    n.is_active and 
                    n.trust_score >= EXCLUDE_THRESHOLD)
            ]

            if potential_destinations:
                dst = random.choice(potential_destinations)
                success = await self.send_encrypted_message(node, dst)
                self.simulation_state["total_messages"] += 1

            await asyncio.sleep(MSG_RATE_PER_NODE)

    async def run_secure_simulation(self, duration_minutes: int = 60):
        """Run the complete secure 100-node simulation"""
        print(f"🚀 Starting {duration_minutes}-minute secure military MANET simulation...")
        self.simulation_state["running"] = True

        # Create tasks for all active nodes
        node_tasks = [
            asyncio.create_task(self.node_communication_loop(node))
            for node in self.nodes if node.trust_score >= EXCLUDE_THRESHOLD
        ]

        # Add security maintenance task
        maintenance_task = asyncio.create_task(self.periodic_security_maintenance())

        # Combine all tasks
        all_tasks = node_tasks + [maintenance_task]

        try:
            await asyncio.wait_for(
                asyncio.gather(*all_tasks, return_exceptions=True),
                timeout=duration_minutes * 60
            )
        except asyncio.TimeoutError:
            print(f"✅ Secure simulation completed after {duration_minutes} minutes")
        except KeyboardInterrupt:
            print("⏹️ Simulation stopped by user")
        finally:
            self.simulation_state["running"] = False

        # Print comprehensive final statistics
        stats = self.get_comprehensive_stats()
        print("\n📊 FINAL SECURE SIMULATION STATISTICS:")
        print(f" • Total Messages: {stats['total_messages']}")
        print(f" • Successful Deliveries: {stats['successful_deliveries']}")
        print(f" • Security Incidents: {stats['anomalies_detected']}")
        print(f" • Blockchain Events: {stats['blockchain_events']}")
        print(f" • Pseudonym Rotations: {stats['pseudonym_rotations']}")
        print(f" • Encryption Operations: {stats['encryption_operations']}")
        print(f" • Network Connectivity: {stats['network_connectivity']:.1f}%")
        print(f" • Average Trust Score: {stats['average_trust']:.1f}")
        print(f" • Low Trust Nodes: {stats['low_trust_nodes']}")

# Main execution
async def main():
    """Main execution function"""
    simulator = SecureMILBASTER()
    simulator.initialize_network()
    await simulator.run_secure_simulation(duration_minutes=5)  # 5-minute demo

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Secure MIL-BASTER simulation terminated.")
    except Exception as e:
        print(f"❌ Simulation error: {e}")