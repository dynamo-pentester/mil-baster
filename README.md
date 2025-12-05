# 🛡️ MIL-BASTER – Military Ad-Hoc Network Security Platform

Next-generation secure routing with dynamic trust management and tamper-proof audit trails for Mobile Ad-hoc Networks (MANETs).

---

## Overview

MIL-BASTER is a research prototype that simulates adversarial MANET environments, detects malicious routing behavior (packet drops and tampering), generates cryptographically verifiable forensic evidence, and secures that evidence using Merkle-tree batching with optional blockchain anchoring. The system demonstrates a complete evidence lifecycle: detection → sign → encrypt → store → batch → anchor.

---

## Key Features (Implemented)

- **Adversarial Routing Simulation** — AODV-inspired multi-hop message forwarding and route simulation.
- **Malicious Behavior Detection** — Automatic detection of packet **drop** and **tamper** events during forwarding.
- **Dynamic Trust Engine** — Reputation scores per node (configurable penalties: tamper = −10, drop = −20); nodes reaching a threshold (0) are classified malicious.
- **Cryptographic Evidence** — Each security event is recorded as a signed (Ed25519) and AES-GCM encrypted evidence package.
- **Local Forensic Store** — Evidence persisted in an on-disk SQLite database for auditability.
- **Merkle Tree Batching** — Periodic Merkle tree construction over evidence; proofs are stored with each evidence item.
- **Blockchain Anchoring (Sepolia)** — Merkle roots can be anchored to Ethereum (Sepolia testnet) via Web3. Anchoring has robust fallback: local cache & retry logic when RPC or keys are unavailable.
- **Secure Key Keystore** — Demo keystore for keys; designed to be replaced with TPM/HSM in production.

---

## What is *not* implemented (and why)

- **Onion Routing (NOT implemented yet)** — The current prototype does **not** perform multi-layer per-hop encryption (onion routing). The project implements end-to-end signed and encrypted evidence logging, but routing messages are forwarded with standard AODV-style behavior. Onion routing is planned as a future enhancement (see Roadmap).

---

## Roadmap / Future Work

Planned features for upcoming milestones:

- **Onion Routing (Future Implementation)**: Multi-layer encryption with per-hop ECDH-derived keys (X25519 + AES-GCM), so intermediate hops cannot read payloads or link source/destination beyond their immediate neighbor.
- **Hardware Key Protection**: TPM/HSM integration for private keys to ensure forensic non-repudiation.
- **Asynchronous Anchor Queue**: Dedicated sender/reconciler to guarantee on-chain anchoring without blocking simulation.
- **Distributed Storage Option**: Integrate IPFS or similar for storing large forensic blobs with on-chain index pointers.
- **Performance Benchmarks**: Latency and bandwidth tests for large topologies and message sizes.

---

## Quick Start

1. Clone:
```bash
git clone https://github.com/dynamo-pentester/mil-baster.git
cd mil-baster
(Optional) Create virtual env:

bash
Copy code
python -m venv venv
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
Install:

bash
Copy code
pip install -r requirements.txt
(Optional) Configure blockchain env in .env:

ini
Copy code
INFURA_SEPOLIA_URL=your_infura_url
PRIVATE_KEY=your_private_key
ACCOUNT=your_account
CONTRACT_ADDR=deployed_contract_address
Run the simulator:

bash
Copy code
python -m src.sim_runner
Example Output
csharp
Copy code
[sim][EVIDENCE] recorded evidence rowid=52 ... offender=node3 action=tamper
[sim][TRUST] Node node3 penalized (-10); new trust=0
Final anchor result: { 'root': 'f147...', 'tx_hash': '0x5936...', 'block_number': 0, 'count': 16 }
Project Structure
css
Copy code
src/
 ├─ sim_runner.py
 ├─ routing.py
 ├─ trust.py
 ├─ crypto_utils.py
 ├─ evidence_manager.py
 ├─ merkle_utils.py
 ├─ web3_utils.py
 ├─ db_utils.py
contracts/
 └─ MILBASTERLog.sol
Verification & Demo
Use tools/verify_evidence.py <rowid> to verify signature + Merkle proof for a saved evidence row.

Inspect milbaster.db to see evidence rows and anchors.

License
MIT — Research prototype. Not for production-critical deployments unless hardened with TPM/HSM and audited.

Contact
0x_Dynamo — Developer & Researcher
