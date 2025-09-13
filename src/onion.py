# onion.py
# Build simple onion for small number of hops using ECDH-derived AES keys

from crypto_utils import derive_shared_key, aes_gcm_encrypt, aes_gcm_decrypt, b64, ub64
from typing import List

# Each hop must already have a shared AES key between sender and that hop.
# For demo, we derive ephemeral shared keys between source and each hop using ephemeral keys.
# build_onion(payload_bytes, hop_pubkeys, src_priv)
def build_onion(payload: bytes, hop_pubkeys: List, src_priv):
    # hop_pubkeys ordered outermost->innermost (first hop, second hop, ...)
    # For each hop derive session key and wrap
    current = payload
    session_info = []
    for pub in reversed(hop_pubkeys):  # innermost first
        session_key = derive_shared_key(src_priv, pub)
        current = aes_gcm_encrypt(session_key, current)
        session_info.append(b64(session_key[:16]))  # debug: DON'T store keys in production
    return current

def peel_onion(onion_blob: bytes, key):
    return aes_gcm_decrypt(key, onion_blob)
