# src/enhanced_models.py
# Enhanced Node model with battlefield positioning for 100-node simulation

import random
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Set, Tuple, List
from .crypto_utils import gen_keypair

@dataclass
class AODVNode:
    """Enhanced Node with AODV protocol support and battlefield positioning"""
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
    unit_type: str = field(default="INFANTRY")  # INFANTRY, ARMOR, AIR, COMMAND
    radio_range: float = field(default=150.0)   # meters
    energy_level: float = field(default=100.0)  # battery %
    
    # Statistics
    stats: Dict[str, int] = field(default_factory=lambda: {
        "sent": 0, "forwarded": 0, "dropped": 0, 
        "rreq_sent": 0, "rrep_sent": 0, "rerr_sent": 0, "hello_sent": 0
    })
    
    # Status
    is_active: bool = True
    pseudonym: str = None

    def __post_init__(self):
        if self.priv is None or self.pub is None:
            p, q = gen_keypair()
            self.priv = p
            self.pub = q
        if self.pseudonym is None:
            self.pseudonym = f"SOLDIER_{self.node_id}"
        
        # Set radio range based on unit type
        range_map = {"INFANTRY": 150, "ARMOR": 200, "AIR": 300, "COMMAND": 250}
        self.radio_range = range_map.get(self.unit_type, 150)

    def distance_to(self, other_node: 'AODVNode') -> float:
        """Calculate Euclidean distance to another node"""
        dx = self.position[0] - other_node.position[0]
        dy = self.position[1] - other_node.position[1]
        return math.sqrt(dx*dx + dy*dy)

    def can_communicate_with(self, other_node: 'AODVNode') -> bool:
        """Check if node is within radio range"""
        return self.distance_to(other_node) <= self.radio_range and self.is_active

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
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
    """Create 100 soldier nodes with realistic battlefield distribution"""
    nodes = []
    unit_types = ["INFANTRY"] * 70 + ["ARMOR"] * 20 + ["AIR"] * 5 + ["COMMAND"] * 5
    
    for i in range(100):
        node = AODVNode(
            node_id=str(i),
            unit_type=unit_types[i],
            position=(
                random.uniform(0, 1000) + random.gauss(0, 50),  # Add some clustering
                random.uniform(0, 1000) + random.gauss(0, 50)
            )
        )
        nodes.append(node)
    
    # Mark 8-9 nodes as randomly malicious
    malicious_count = random.randint(8, 9)
    malicious_nodes = random.sample(nodes, malicious_count)
    for node in malicious_nodes:
        node.malicious = True
        print(f"🚨 THREAT DETECTED: Node {node.node_id} ({node.unit_type}) marked as malicious")
    
    return nodes
