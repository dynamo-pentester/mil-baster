# aodv_protocol.py
# AODV Protocol messages: RREQ, RREP, RERR, HELLO

import time
from dataclasses import dataclass, field
from typing import List, Optional
from .models import AODVNode

@dataclass
class AODVMessage:
    """Base AODV message"""
    src_id: str
    dst_id: str
    msg_type: str = field(init=False)
    timestamp: float = field(default_factory=time.time, init=False)

@dataclass  
class RouteRequest(AODVMessage):
    """RREQ - Route Request message"""
    rreq_id: int
    hop_count: int = 0
    src_seq: int = 0
    dst_seq: int = 0
    
    def __post_init__(self):
        self.msg_type = "RREQ"

@dataclass
class RouteReply(AODVMessage):
    """RREP - Route Reply message"""
    dst_seq: int
    hop_count: int = 0
    lifetime: float = 30.0  # seconds
    
    def __post_init__(self):
        self.msg_type = "RREP"

@dataclass
class RouteError(AODVMessage):
    """RERR - Route Error message"""
    broken_nodes: List[str]
    
    def __post_init__(self):
        self.msg_type = "RERR"

@dataclass
class HelloMessage(AODVMessage):
    """HELLO - Neighbor discovery message"""
    position: tuple
    energy_level: float
    
    def __post_init__(self):
        self.msg_type = "HELLO"
        self.dst_id = "BROADCAST"

class AODVProtocol:
    """AODV Protocol implementation"""
    
    def __init__(self, node: AODVNode):
        self.node = node
        self.route_cache_timeout = 30.0  # seconds
        self.hello_interval = 5.0        # seconds
        self.last_hello = 0
    
    async def send_hello(self, neighbors: List[AODVNode]):
        """Send HELLO message to discover/maintain neighbors"""
        if time.time() - self.last_hello < self.hello_interval:
            return
        
        hello_msg = HelloMessage(
            src_id=self.node.node_id,
            dst_id="BROADCAST",
            position=self.node.position,
            energy_level=self.node.energy_level
        )
        
        # Update neighbors based on radio range
        new_neighbors = set()
        for neighbor in neighbors:
            if (neighbor.node_id != self.node.node_id and 
                self.node.can_communicate_with(neighbor)):
                new_neighbors.add(neighbor.node_id)
        
        self.node.neighbors = new_neighbors
        self.node.stats["hello_sent"] += 1
        self.last_hello = time.time()
        
        return hello_msg
    
    def find_route_to(self, dst_id: str) -> Optional[List[str]]:
        """Find cached route to destination"""
        if dst_id in self.node.routing_table:
            route_entry = self.node.routing_table[dst_id]
            # Check if route is still valid
            if time.time() - route_entry.get("timestamp", 0) < self.route_cache_timeout:
                return route_entry.get("path", [])
        return None
    
    async def send_rreq(self, dst_id: str, all_nodes: List[AODVNode]) -> RouteRequest:
        """Send Route Request to find path to destination"""
        self.node.rreq_id += 1
        self.node.sequence_number += 1
        
        rreq = RouteRequest(
            src_id=self.node.node_id,
            dst_id=dst_id,
            rreq_id=self.node.rreq_id,
            src_seq=self.node.sequence_number,
            hop_count=0
        )
        
        self.node.stats["rreq_sent"] += 1
        return rreq
    
    async def handle_rreq(self, rreq: RouteRequest, sender_id: str) -> Optional[RouteReply]:
        """Handle incoming RREQ"""
        # If we're the destination, send RREP
        if rreq.dst_id == self.node.node_id:
            self.node.sequence_number = max(self.node.sequence_number, rreq.dst_seq) + 1
            
            rrep = RouteReply(
                src_id=self.node.node_id,
                dst_id=rreq.src_id,
                dst_seq=self.node.sequence_number,
                hop_count=0
            )
            
            self.node.stats["rrep_sent"] += 1
            return rrep
        
        return None
    
    def update_routing_table(self, dst_id: str, next_hop: str, hop_count: int, seq_num: int):
        """Update routing table entry"""
        self.node.routing_table[dst_id] = {
            "next_hop": next_hop,
            "hop_count": hop_count,
            "seq_num": seq_num,
            "timestamp": time.time(),
            "path": [self.node.node_id, next_hop, dst_id]  # Simplified path
        }
