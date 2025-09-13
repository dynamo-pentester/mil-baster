# routing.py
# Route selection logic: choose random path avoiding low-trust nodes

import random
from typing import List
from models import Node

def choose_route(nodes: List[Node], src: Node, dst: Node, hops=3, exclude_below=50):
    # build candidate set excluding low-trust and the src/dst
    candidates = [n for n in nodes if n.node_id not in (src.node_id, dst.node_id) and n.trust_score >= exclude_below]
    route = [src]
    # pick up to hops intermediates
    if candidates:
        inter = random.sample(candidates, k=min(len(candidates), hops))
        route.extend(inter)
    route.append(dst)
    return route
