# tools/verify_evidence.py
import argparse
from src.db_utils import get_evidence_by_id
from src.crypto_utils import derive_node_symmetric_key, aes_gcm_decrypt, load_node_public_bytes, verify_signature, sha256_hex
from src.web3_utils import get_web3
import json

def verify(rowid: int):
    rec = get_evidence_by_id(rowid)
    if not rec:
        print("No record")
        return False
    # parse stored blob
    blob = rec["encrypted_blob"]
    # split nonce(12) + tag(16) + ciphertext
    nonce = blob[0:12]
    tag = blob[12+ (len(blob)-28):12+ (len(blob)-12)] if False else blob[12:12+16]  # simpler: next 16 bytes after nonce
    # However our storage format was nonce + tag + ciphertext, so:
    tag = blob[12:28]
    ciphertext = blob[28:]
    node_id = rec["signer_id"]
    key = derive_node_symmetric_key(node_id, peer_pubkey_bytes=None)  # adjust if you used peer pub
    try:
        clear = aes_gcm_decrypt(key, nonce, tag, ciphertext)
    except Exception as e:
        print("Decryption failed:", e)
        return False
    package = json.loads(clear)
    evidence_bytes = json.dumps(package["evidence"], separators=(",", ":"), sort_keys=True).encode()
    signature_hex = package["signature"]
    signer_id = package["signer_id"]
    pub = load_node_public_bytes(signer_id)
    ok = verify_signature(pub, evidence_bytes, bytes.fromhex(signature_hex))
    print("Signature verification:", ok)
    # merkle proof check against on-chain root (if we have tx_hash)
    if rec.get("tx_hash"):
        w3 = get_web3()
        if not w3:
            print("No web3 configured locally; cannot fetch on-chain root")
            return ok
        # recover root from the tx data
        tx = w3.eth.get_transaction(rec["tx_hash"])
        data_hex = tx.input
        root_onchain = w3.toText(hexstr=data_hex)
        # compute leaf hash and validate proof
        import hashlib
        leaf_hash = hashlib.sha256(rec["encrypted_blob"]).hexdigest()
        proof = rec["merkle_proof"]
        # validate merkle proof using pymerkle
        from src.merkle_utils import validate_proof
        ok2 = validate_proof(leaf_hash, proof, root_onchain)
        print("Merkle proof valid against on-chain root:", ok2)
        return ok and ok2
    else:
        print("No tx_hash recorded for this evidence row; only signature verified:", ok)
        return ok

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("id", type=int)
    args = p.parse_args()
    res = verify(args.id)
    print("VERIFICATION RESULT:", res)
