import time
from .db_utils import save_trust

def update_trust(node, delta, reason):
    node.trust_score = max(0, min(100, node.trust_score + delta))
    save_trust(node.node_id, node.trust_score, reason, int(time.time()))
    return node.trust_score
