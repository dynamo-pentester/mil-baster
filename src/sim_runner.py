# src/sim_runner_100.py  
# Main 100-node AODV simulation with dashboard integration

import asyncio
import time
import json
import random
from typing import List, Dict
from .models import AODVNode, create_100_nodes
from .aodv_protocol import AODVProtocol, RouteRequest, RouteReply
from .crypto_utils import sign_message, aes_gcm_encrypt, derive_shared_key, sha256_hex
from .db_utils import init_db, save_evidence, save_trust
from .trust import update_trust

# Enhanced simulation parameters  
MSG_RATE_PER_NODE = 0.5        # Reduced rate for 100 nodes
MALICIOUS_DROP_RATE = 0.7      # 70% drop rate for malicious nodes
TRUST_DECREMENT = -15          # Penalty for anomalies
TRUST_INCREMENT = 1            # Reward for good behavior
EXCLUDE_THRESHOLD = 40         # Exclude nodes below this trust
HELLO_INTERVAL = 5.0           # HELLO message interval

class EnhancedMILBASTER:
    """Enhanced MIL-BASTER simulation with 100 nodes"""
    
    def __init__(self):
        self.nodes: List[AODVNode] = []
        self.protocols: Dict[str, AODVProtocol] = {}
        self.simulation_state = {
            "running": False,
            "total_messages": 0,
            "successful_deliveries": 0,
            "anomalies_detected": 0,
            "blockchain_events": 0,
            "network_connectivity": 0.0
        }
    
    def initialize_network(self):
        """Initialize 100-node military network"""
        print("🏗️ Initializing 100-node military MANET...")
        init_db()
        
        # Create 100 soldier nodes
        self.nodes = create_100_nodes()
        
        # Initialize AODV protocols
        for node in self.nodes:
            self.protocols[node.node_id] = AODVProtocol(node)
        
        # Calculate initial network topology
        self.update_network_topology()
        
        print(f"✅ Network initialized: {len(self.nodes)} soldiers deployed")
        print(f"   • Infantry: {len([n for n in self.nodes if n.unit_type == 'INFANTRY'])}")
        print(f"   • Armor: {len([n for n in self.nodes if n.unit_type == 'ARMOR'])}")  
        print(f"   • Air Support: {len([n for n in self.nodes if n.unit_type == 'AIR'])}")
        print(f"   • Command: {len([n for n in self.nodes if n.unit_type == 'COMMAND'])}")
        print(f"   • Malicious: {len([n for n in self.nodes if n.malicious])}")
    
    def update_network_topology(self):
        """Update neighbor relationships based on radio range"""
        for node in self.nodes:
            neighbors = []
            for other_node in self.nodes:
                if node.can_communicate_with(other_node):
                    neighbors.append(other_node)
            
            # Update protocol neighbors
            protocol = self.protocols[node.node_id]
            asyncio.create_task(protocol.send_hello(neighbors))
    
    async def simulate_aodv_routing(self, src: AODVNode, dst: AODVNode) -> List[AODVNode]:
        """Simulate AODV route discovery"""
        src_protocol = self.protocols[src.node_id]
        
        # Check for cached route
        cached_route = src_protocol.find_route_to(dst.node_id)
        if cached_route:
            route_nodes = [self.get_node_by_id(node_id) for node_id in cached_route]
            return [node for node in route_nodes if node]  # Filter None values
        
        # Send RREQ for route discovery
        rreq = await src_protocol.send_rreq(dst.node_id, self.nodes)
        
        # Simulate route discovery (simplified)
        # In real AODV, this would flood the network
        intermediate_nodes = [
            node for node in self.nodes 
            if (node.node_id not in (src.node_id, dst.node_id) and 
                node.trust_score >= EXCLUDE_THRESHOLD and
                not node.malicious)
        ]
        
        if intermediate_nodes:
            # Select 2-3 intermediate nodes for multi-hop route
            num_hops = min(3, len(intermediate_nodes))
            selected_intermediates = random.sample(intermediate_nodes, num_hops)
            route = [src] + selected_intermediates + [dst]
        else:
            route = [src, dst]
        
        return route
    
    async def send_message(self, src: AODVNode, dst: AODVNode):
        """Send encrypted message through AODV route"""
        # Discover route using AODV
        route = await self.simulate_aodv_routing(src, dst)
        
        if len(route) < 2:
            return False
        
        # Create encrypted message payload
        payload = {
            "from": src.pseudonym,
            "to": dst.pseudonym, 
            "message": f"TACTICAL_MSG_{int(time.time())}",
            "priority": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "timestamp": time.time()
        }
        
        # Simulate message forwarding through route
        for i, hop in enumerate(route[1:], 1):  # Skip source
            if hop.malicious and random.random() < MALICIOUS_DROP_RATE:
                # Malicious node drops packet
                await self.handle_packet_drop(hop, route, payload)
                return False
            else:
                # Successful forwarding
                hop.stats["forwarded"] += 1
                update_trust(hop, TRUST_INCREMENT, "successful_forward")
        
        # Message delivered successfully
        self.simulation_state["successful_deliveries"] += 1
        src.stats["sent"] += 1
        return True
    
    async def handle_packet_drop(self, malicious_node: AODVNode, route: List[AODVNode], payload: Dict):
        """Handle malicious packet dropping with evidence logging"""
        malicious_node.stats["dropped"] += 1
        self.simulation_state["anomalies_detected"] += 1
        
        # Create encrypted evidence
        evidence = {
            "event": "packet_drop",
            "malicious_node": malicious_node.node_id,
            "route": [node.node_id for node in route],
            "payload_hash": sha256_hex(json.dumps(payload).encode()),
            "timestamp": time.time(),
            "position": malicious_node.position,
            "unit_type": malicious_node.unit_type
        }
        
        # Encrypt and store evidence
        evidence_bytes = json.dumps(evidence).encode()
        encryption_key = b"demo_key_32_bytes_for_evidence_enc"  # In production: use proper key derivation
        encrypted_evidence = aes_gcm_encrypt(encryption_key, evidence_bytes)
        event_hash = sha256_hex(encrypted_evidence)
        
        save_evidence(event_hash, encrypted_evidence, int(time.time()))
        
        # Update trust score
        new_trust = update_trust(malicious_node, TRUST_DECREMENT, "packet_drop_detected")
        
        print(f"🚨 THREAT DETECTED: {malicious_node.unit_type} {malicious_node.node_id} "
              f"dropped packet. Trust: {new_trust}. Hash: {event_hash[:12]}...")
    
    def get_node_by_id(self, node_id: str) -> AODVNode:
        """Get node by ID"""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None
    
    def get_network_stats(self) -> Dict:
        """Get current network statistics"""
        total_nodes = len(self.nodes)
        active_nodes = len([n for n in self.nodes if n.is_active])
        malicious_nodes = len([n for n in self.nodes if n.malicious])
        avg_trust = sum(n.trust_score for n in self.nodes) / total_nodes
        
        return {
            "total_nodes": total_nodes,
            "active_nodes": active_nodes, 
            "malicious_nodes": malicious_nodes,
            "average_trust": avg_trust,
            "network_connectivity": self.calculate_connectivity(),
            **self.simulation_state
        }
    
    def calculate_connectivity(self) -> float:
        """Calculate network connectivity percentage"""
        if not self.nodes:
            return 0.0
        
        total_possible_connections = len(self.nodes) * (len(self.nodes) - 1) // 2
        actual_connections = 0
        
        for i, node1 in enumerate(self.nodes):
            for node2 in self.nodes[i+1:]:
                if node1.can_communicate_with(node2):
                    actual_connections += 1
        
        return (actual_connections / total_possible_connections) * 100 if total_possible_connections > 0 else 0.0
    
    async def node_communication_loop(self, node: AODVNode):
        """Individual node communication loop"""
        while self.simulation_state["running"]:
            if not node.is_active:
                await asyncio.sleep(MSG_RATE_PER_NODE)
                continue
                
            # Select random destination
            potential_destinations = [n for n in self.nodes 
                                    if n.node_id != node.node_id and n.is_active]
            
            if potential_destinations:
                dst = random.choice(potential_destinations)
                success = await self.send_message(node, dst)
                self.simulation_state["total_messages"] += 1
            
            await asyncio.sleep(MSG_RATE_PER_NODE)
    
    async def network_maintenance_loop(self):
        """Maintain network topology and update metrics"""
        while self.simulation_state["running"]:
            # Update network topology
            self.update_network_topology()
            
            # Randomly reassign malicious nodes (simulate changing threats)
            if random.random() < 0.05:  # 5% chance per maintenance cycle
                await self.reassign_malicious_nodes()
            
            await asyncio.sleep(10.0)  # Update every 10 seconds
    
    async def reassign_malicious_nodes(self):
        """Randomly reassign malicious nodes to simulate dynamic threats"""
        # Clear current malicious status
        for node in self.nodes:
            node.malicious = False
        
        # Reassign 8-9 malicious nodes
        malicious_count = random.randint(8, 9)
        malicious_nodes = random.sample(self.nodes, malicious_count)
        
        for node in malicious_nodes:
            node.malicious = True
            print(f"⚠️ NEW THREAT: Node {node.node_id} ({node.unit_type}) turned malicious")
    
    async def run_simulation(self, duration_minutes: int = 60):
        """Run the complete 100-node simulation"""
        print(f"🚀 Starting {duration_minutes}-minute military MANET simulation...")
        
        self.simulation_state["running"] = True
        
        # Create tasks for all nodes
        node_tasks = [
            asyncio.create_task(self.node_communication_loop(node)) 
            for node in self.nodes
        ]
        
        # Add maintenance task
        maintenance_task = asyncio.create_task(self.network_maintenance_loop())
        
        # Run simulation for specified duration
        try:
            await asyncio.wait_for(
                asyncio.gather(*node_tasks, maintenance_task),
                timeout=duration_minutes * 60
            )
        except asyncio.TimeoutError:
            print(f"✅ Simulation completed after {duration_minutes} minutes")
        except KeyboardInterrupt:
            print("⏹️ Simulation stopped by user")
        finally:
            self.simulation_state["running"] = False
            
            # Print final statistics
            stats = self.get_network_stats()
            print("\n📊 FINAL SIMULATION STATISTICS:")
            print(f"   • Total Messages: {stats['total_messages']}")
            print(f"   • Successful Deliveries: {stats['successful_deliveries']}")
            print(f"   • Anomalies Detected: {stats['anomalies_detected']}")
            print(f"   • Network Connectivity: {stats['network_connectivity']:.1f}%")
            print(f"   • Average Trust Score: {stats['average_trust']:.1f}")

# Main execution
async def main():
    simulator = EnhancedMILBASTER()
    simulator.initialize_network()
    await simulator.run_simulation(duration_minutes=10)  # 10-minute demo

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ MIL-BASTER simulation terminated.")
