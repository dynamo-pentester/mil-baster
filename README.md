# 🛡️ MIL-BASTER: Military-Grade Blockchain-Assisted Secure Routing

**Next-generation secure routing with dynamic trust management and tamper-proof audit trails for Mobile Ad-hoc Networks (MANETs)**

## 🎯 **Problem Statement**

Military communication networks are vulnerable to:
- ❌ Malicious nodes dropping/tampering packets
- ❌ No trust management to exclude bad actors
- ❌ No tamper-proof audit of anomalies
- ❌ Identity/location leaks if devices captured

## ⚡ **Our Solution**

**MIL-BASTER** provides:
- ✅ **Real-time anomaly detection** (sliding window analysis)
- ✅ **Dynamic trust scoring** (-20 drop, +1 success, exclude <50)
- ✅ **Onion routing** with ECC encryption (ECDSA + ECDH → AES)
- ✅ **Blockchain audit trail** (tamper-proof event logs)
- ✅ **Adaptive routing** (excludes untrustworthy nodes)
- deployed using REMIX IDE
- <img width="1919" height="971" alt="image" src="https://github.com/user-attachments/assets/46ad9e9e-cbfd-41bb-9362-99c5672e7c43" />

## 🚀 **Quick Start**

    1. Clone repository
    git clone https://github.com/dynamo-pentester/mil-baster.git
    cd mil-baster

    2. Setup environment
    python -m venv venv
    source venv/bin/activate # Windows: venv\Scripts\activate

    3. Install dependencies
    pip install -r requirements.txt

    4. Configure environment variables (optional for blockchain features)
    # Create .env file with:
    INFURA_SEPOLIA_URL=your_infura_sepolia_rpc_url
    DEMO_PRIVATE_KEY=your_private_key
    DEMO_ACCOUNT=your_account_address
    CONTRACT_ADDR=deployed_contract_address

    5. Run simulation
    python -m src.sim_runner

## 🔐 **Technology Stack**
- **Simulation**: Python 3.11 + asyncio
- **Cryptography**: ECDSA signatures, ECDH key exchange, AES-GCM
- **Database**: SQLite (local), PostgreSQL (production)
- **Blockchain**: Solidity + Web3.py → Sepolia testnet
- **Monitoring**: Real-time trust scoring + anomaly detection
- **Web Dashboard**: Flask + SocketIO + Plotly

## 📊 **Demo Output**
🎯 SIMULATION STARTED: 6 nodes, Node 5 is malicious
[ANOMALY] 🚨 Node 5 dropped packet from 0→4, Trust: 100 → 80
[TRUST] 🔒 Excluding low-trust nodes ['5'] from routing

## 🏗️ **Architecture**
[MANET Nodes] → [Anomaly Detection] → [Trust Engine] → [SQLite DB]
↓
[Blockchain Logger] → [Sepolia Testnet]

## 📈 **Key Features**
- **Trust Management**: Dynamic scoring with automatic exclusion
- **Cryptographic Security**: Military-grade ECC + AES encryption
- **Blockchain Audit**: Tamper-proof event logging on Sepolia
- **Network Resilience**: Self-healing routes around malicious nodes
- **Web Dashboard**: Real-time monitoring and visualization
- **Pseudonym Rotation**: Privacy-preserving identity management

## 📁 **Project Structure**
- `src/`: Core simulation and protocol implementation
  - `sim_runner.py`: Main simulation orchestrator
  - `aodv_protocol.py`: AODV routing protocol with security extensions
  - `models.py`: Node and network models
  - `crypto_utils.py`: Cryptographic utilities
  - `web3_utils.py`: Blockchain integration
  - `trust.py`: Trust scoring system
  - `monitoring.py`: Anomaly detection
  - `db_utils.py`: Database operations
- `contracts/`: Smart contract source code
- `dashboard/`: Web dashboard frontend and backend
- `scripts/`: Deployment and demo scripts
- `MILBASTERLog_abi.json`: ABI for the smart contract

## 🌐 **Web Dashboard**
Start the real-time monitoring dashboard:
```
python dashboard/app.py
```
Access at http://localhost:5000 for live network visualization.

## 🧪 **Testing**
Run unit tests:
```
pytest
```

## 🤝 **Contributing**
Contributions welcome! Please open issues or PRs for improvements.

## 📄 **License**
MIT License

---
*Built for defense-grade deployment in UAV swarms, soldier mesh networks, and vehicle-to-vehicle networks*

