# 🛡️ MIL-BASTER: Military-Grade Blockchain-Assisted Secure Routing

Next-generation secure routing with dynamic trust management and tamper-proof audit trails for Mobile Ad-hoc Networks (MANETs)

![Intro](https://media.giphy.com/media/du3J3cXyzhj75IOgvA/giphy.gif)

## 🎯 Problem Statement

Military communication networks are highly susceptible to sophisticated threats, including data tampering, packet dropping, and identity compromise. Current solutions lack a robust, dynamic trust management system and a tamper-proof mechanism for auditing network anomalies, making them vulnerable to insider attacks and operational disruptions.

## ⚡ Our Solution

MIL-BASTER is a comprehensive security framework for Mobile Ad-hoc Networks (MANETs) that integrates real-time anomaly detection, dynamic trust management, and a blockchain-based audit trail. This solution ensures the integrity, confidentiality, and resilience of critical communication, providing a self-healing and secure network environment for military applications.

Key Features:
- Real-time Anomaly Detection: Utilizes a sliding window analysis to immediately identify and flag anomalous behavior, such as dropped packets or unauthorized data manipulation.

![Detection](https://github.com/user-attachments/assets/c53140aa-2a55-4ad5-840d-b7edb7737b29)

- Dynamic Trust Scoring: Employs a reputation-based system where each node's trust score is dynamically adjusted based on its network behavior.

![Trust](https://media.giphy.com/media/l41lVsYDBC0UVQJCE/giphy.gif)

Successful packet transmission: +1 point

Packet drop or tampering: -20 points

Nodes with a score below 50 are automatically excluded from routing.

- Onion Routing with ECC Encryption: Provides a multi-layered cryptographic approach to secure data.

![Encryption](https://github.com/user-attachments/assets/8afbd3c3-0bbb-4197-81d8-8f98f4b66f66)

ECDSA Signatures: Ensures data origin authentication and integrity.

ECDH Key Exchange: Establishes secure, ephemeral session keys between nodes.

AES-GCM: Guarantees confidentiality and authenticated encryption of the data payload.

- Blockchain Audit Trail: All security-relevant events, including trust score updates and anomaly logs, are recorded on a blockchain. This provides a decentralized, tamper-proof, and transparent record for forensic analysis and accountability.

- Adaptive Routing: The system intelligently selects the most trustworthy and efficient routing paths, dynamically adapting to exclude compromised or low-trust nodes, thereby enhancing network resilience.

## 🚀 Quick Start

To run the MIL-BASTER simulation, follow these steps:

1. Clone the repository:
```
git clone https://github.com/dynamo-pentester/mil-baster.git
cd mil-baster
```

2. Set up the Python virtual environment:
```
python -m venv venv
source venv/bin/activate  # Use 'venv\Scripts\activate' on Windows
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```

4. Configure environment variables (optional for blockchain features):
Create a `.env` file with:
```
INFURA_SEPOLIA_URL=your_infura_sepolia_rpc_url
DEMO_PRIVATE_KEY=your_private_key
DEMO_ACCOUNT=your_account_address
CONTRACT_ADDR=deployed_contract_address
```

5. Run the simulation:
```
python -m src.sim_runner
```

## 🔐 Technology Stack

- Simulation: Python 3.11 with asyncio for concurrent network simulations.
- Cryptography: Implemented using industry-standard libraries for ECDSA, ECDH, and AES-GCM.
- Database: SQLite for local node data persistence and PostgreSQL for scalable, production-grade network-wide data management.
- Blockchain: A custom Solidity smart contract is deployed on the Sepolia test network, with interactions managed via Web3.py.
- Monitoring: Real-time dashboards and logs provide insights into trust scores and anomaly detection events.
- Web Dashboard: Flask + SocketIO + Plotly for real-time visualization.

## 📊 Demo Output

🎯 SIMULATION STARTED: 100 nodes, several malicious nodes present
[ANOMALY] 🚨 Node 45 dropped packet from 12→78, Trust: 100 → 80
[TRUST] 🔒 Excluding low-trust nodes from routing

## 🏗️ Architecture

The MIL-BASTER architecture is designed for modularity and scalability. Each network node runs a micro-service-based stack:

[MANET Nodes] → [Anomaly Detection] → [Trust Engine] → [SQLite DB]
↓
[Blockchain Integration]

- MANET Nodes: Simulates the physical hardware, including communication interfaces.
- Anomaly Detection: A service that monitors packet flow and network behavior.
- Trust Engine: A core service that calculates and updates node trust scores.
- SQLite DB: Stores local trust scores and historical data for quick access.
- Blockchain Integration: A service responsible for hashing and logging critical events onto the Sepolia testnet.

## 📁 Project Structure

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

## 🌐 Web Dashboard

Start the real-time monitoring dashboard:
```
run dashboard.html
```
Access at http://localhost:5000 for live network visualization.

## 🧪 Testing

Run unit tests:
```
pytest
```

## 🤝 Contributing

Contributions welcome! Please open issues or PRs for improvements.

## 📄 License

MIT License

---
Built for defense-grade deployment in UAV swarms, soldier mesh networks, and vehicle-to-vehicle communication.



