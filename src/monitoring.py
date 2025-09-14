# monitoring.py
# Sliding-window anomaly detector

import time
from collections import deque, defaultdict
from typing import Deque, Dict, Tuple

class SlidingWindowMonitor:
    def __init__(self, window_msgs=20, window_seconds=30):
        self.window_msgs = window_msgs
        self.window_seconds = window_seconds
        self.records: Dict[str, Deque] = defaultdict(deque)

    def record(self, node_id: str, forwarded: bool):
        now = int(time.time())
        dq = self.records[node_id]
        dq.append((now, forwarded))
        while dq and (len(dq) > self.window_msgs or (now - dq[0][0]) > self.window_seconds):
            dq.popleft()

    def drop_rate(self, node_id: str) -> float:
        dq = self.records[node_id]
        total = len(dq)
        if total == 0:
            return 0.0
        forwarded = sum(1 for _, f in dq if f)
        return (total - forwarded) / total

    def is_anomalous(self, node_id: str, threshold: float = 0.3) -> Tuple[bool, float]:
        rate = self.drop_rate(node_id)
        return rate > threshold, rate
