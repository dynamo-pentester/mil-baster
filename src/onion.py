from .crypto_utils import derive_shared_key, aes_gcm_encrypt, aes_gcm_decrypt, b64, ub64
from typing import List

def build_onion(payload: bytes, hop_pubkeys: List, src_priv):
    current = payload
    for pub in reversed(hop_pubkeys):
        key = derive_shared_key(src_priv, pub)
        current = aes_gcm_encrypt(key, current)
    return current

def peel_onion(onion_blob: bytes, key):
    return aes_gcm_decrypt(key, onion_blob)

