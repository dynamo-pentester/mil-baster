# crypto_utils.py
# ECC/ECDH/ECDSA helpers, AES-GCM, key derivation, small helpers.

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
import hashlib
from typing import Tuple

# ECDSA / ECDH key generation (P-256)
def gen_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    return priv, pub

def privkey_to_pem(priv: ec.EllipticCurvePrivateKey) -> bytes:
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

def pubkey_to_pem(pub: ec.EllipticCurvePublicKey) -> bytes:
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def load_pubkey_from_pem(pem_bytes: bytes):
    return serialization.load_pem_public_key(pem_bytes)

# ECDSA sign/verify
def sign_message(priv: ec.EllipticCurvePrivateKey, message_bytes: bytes) -> bytes:
    return priv.sign(message_bytes, ec.ECDSA(hashes.SHA256()))

def verify_signature(pub, message_bytes: bytes, signature: bytes) -> bool:
    try:
        pub.verify(signature, message_bytes, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False

# ECDH ephemeral shared key derivation
def derive_shared_key(priv: ec.EllipticCurvePrivateKey, peer_pub, length=32) -> bytes:
    shared = priv.exchange(ec.ECDH(), peer_pub)
    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=b"mil-baster session key",
    ).derive(shared)
    return derived

# AES-GCM helpers (key must be 16/24/32 bytes)
def aes_gcm_encrypt(key: bytes, plaintext: bytes, aad: bytes = None) -> bytes:
    if len(key) not in (16, 24, 32):
        raise ValueError("AESGCM key must be 128, 192, or 256 bits (16/24/32 bytes)")
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce + ct

def aes_gcm_decrypt(key: bytes, nonce_and_ct: bytes, aad: bytes = None) -> bytes:
    if len(key) not in (16, 24, 32):
        raise ValueError("AESGCM key must be 128, 192, or 256 bits (16/24/32 bytes)")
    aesgcm = AESGCM(key)
    nonce = nonce_and_ct[:12]
    ct = nonce_and_ct[12:]
    return aesgcm.decrypt(nonce, ct, aad)

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# base64 helpers
def b64(x: bytes) -> str:
    return base64.b64encode(x).decode()

def ub64(s: str) -> bytes:
    return base64.b64decode(s.encode())

# AES key helpers
def generate_aes_key(bits: int = 256) -> bytes:
    if bits not in (128, 192, 256):
        raise ValueError("bits must be 128,192,256")
    return os.urandom(bits // 8)

def derive_aes_key(passphrase: str, bits: int = 256) -> bytes:
    if bits not in (128, 192, 256):
        raise ValueError("bits must be 128,192,256")
    # simple deterministic derivation for demo (SHA256)
    full = hashlib.sha256(passphrase.encode()).digest()
    return full[: bits // 8]
