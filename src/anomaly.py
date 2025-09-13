# anomaly.py
# Sliding-window anomaly detection per neighbor

import time
from collections import deque, defaultdict
from typing import Dict, Deque

class SlidingWindowMonitor:
    def __init__(self, window_msgs=20, window_seconds=30):
        self.window_msgs = window_msgs
        self.window_seconds = window_seconds
        # per-node deque of (timestamp, forwarded_bool)
        self.records = defaultdict(lambda: deque())

    def record_forward(self, node_id: str, forwarded: bool):
        now = int(time.time())
        dq: Deque = self.records[node_id]
        dq.append((now, forwarded))
        # pop old
        while dq and ((len(dq) > self.window_msgs) or (now - dq[0][0] > self.window_seconds)):
            dq.popleft()

    def compute_drop_rate(self, node_id: str):
        dq: Deque = self.records[node_id]
        if not dq:
            return 0.0
        total = len(dq)
        forwarded = sum(1 for t,f in dq if f)
        dropped = total - forwarded
        return dropped / total

    def is_anomalous(self, node_id: str, drop_threshold=0.3):
        rate = self.compute_drop_rate(node_id)
        return rate > drop_threshold, rate
