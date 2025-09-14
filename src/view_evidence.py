# view_evidence.py
import sqlite3
import json
import time
from crypto_utils import aes_gcm_decrypt, derive_aes_key

# Derive the same key used in sim_runner
EVIDENCE_KEY = derive_aes_key("mil-baster-evidence", 256)

def view_all_evidence():
    conn = sqlite3.connect("milbaster.db")
    cur = conn.cursor()

    cur.execute("SELECT id, event_hash, encrypted_evidence, created_at FROM evidence")
    rows = cur.fetchall()

    for row in rows:
        evidence_id, event_hash, encrypted, created_at = row
        try:
            decrypted = aes_gcm_decrypt(EVIDENCE_KEY, encrypted)
            evidence = json.loads(decrypted.decode())

            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at))

            print(f"\n📂 Evidence #{evidence_id} (hash={event_hash[:12]}..., time={ts}):")
            print(json.dumps(evidence, indent=2))
        except Exception as e:
            print(f"\n❌ Could not decrypt evidence #{evidence_id}: {e}")

    conn.close()

if __name__ == "__main__":
    view_all_evidence()
