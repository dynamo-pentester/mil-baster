# models.py
# Node class and simple route representation

import time
from dataclasses import dataclass, field
from typing import Dict, Any
from crypto_utils import gen_keypair, privkey_to_pem, pubkey_to_pem

@dataclass
class Node:
    node_id: str
    priv: Any = field(default=None)
    pub: Any = field(default=None)
    trust_score: int = 100
    malicious: bool = False
    stats: Dict[str,int] = field(default_factory=lambda: {"sent":0,"forwarded":0,"dropped":0})
    pseudonym: str = None

    def __post_init__(self):
        if self.priv is None or self.pub is None:
            p, q = gen_keypair()
            self.priv = p
            self.pub = q
        if self.pseudonym is None:
            self.pseudonym = f"pseud_{self.node_id}"

    def to_public_dict(self):
        return {"node_id": self.node_id, "trust_score": self.trust_score, "pseudonym": self.pseudonym}
