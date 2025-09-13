# crypto_utils.py
# Utilities: ECDSA sign/verify, ECDH ephemeral key derivation, AES GCM encrypt/decrypt, SHA256 hash

from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import json
import base64
import hashlib

# ECDSA key generation (P-256)
def gen_keypair():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()
    return priv, pub

def privkey_to_pem(priv):
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

def pubkey_to_pem(pub):
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def sign_message(priv, message_bytes: bytes) -> bytes:
    signature = priv.sign(message_bytes, ec.ECDSA(hashes.SHA256()))
    return signature

def verify_signature(pub, message_bytes: bytes, signature: bytes) -> bool:
    try:
        pub.verify(signature, message_bytes, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False

# ECDH ephemeral shared key derivation
def derive_shared_key(priv, peer_pub, length=32) -> bytes:
    shared = priv.exchange(ec.ECDH(), peer_pub)
    # HKDF to derive symmetric key
    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=b"mil-baster session key",
    ).derive(shared)
    return derived

# AES-GCM encryption / decryption helpers
def aes_gcm_encrypt(key: bytes, plaintext: bytes, aad: bytes = None):
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce + ct  # prefix nonce

def aes_gcm_decrypt(key: bytes, nonce_and_ct: bytes, aad: bytes = None):
    aesgcm = AESGCM(key)
    nonce = nonce_and_ct[:12]
    ct = nonce_and_ct[12:]
    return aesgcm.decrypt(nonce, ct, aad)

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# helper for JSON-safe base64 encoding
def b64(x: bytes) -> str:
    return base64.b64encode(x).decode()

def ub64(s: str) -> bytes:
    return base64.b64decode(s.encode())
