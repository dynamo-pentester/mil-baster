# src/check_block.py
import os
import json
from web3 import Web3
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

RPC_URL = os.getenv("INFURA_SEPOLIA_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDR")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ACCOUNT = os.getenv("ACCOUNT")
ABI_PATH = os.path.join(os.path.dirname(__file__), "../MILBASTERLog_abi.json")
LOCAL_LOG_FILE = os.path.join(os.path.dirname(__file__), "local_chain_log.json")

# Load ABI
if not os.path.exists(ABI_PATH):
    raise FileNotFoundError(f"ABI file not found: {ABI_PATH}")
with open(ABI_PATH, "r") as f:
    ABI = json.load(f)

# Connect to Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))
print(f"✅ Connected to RPC: {RPC_URL[:60]}...")
if not web3.is_connected():
    raise SystemExit("❌ Failed to connect to Ethereum RPC")

# Initialize contract
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
print(f"✅ Contract initialized at {CONTRACT_ADDRESS}")

# Prepare account
account = None
if PRIVATE_KEY:
    account = web3.eth.account.from_key(PRIVATE_KEY)
else:
    print("⚠️ No PRIVATE_KEY found, using local-only mode (no blockchain push)")

# Sample log event
event = {
    "eventHash": "TEST_EVENT_001",
    "anomalyType": 2,
    "trustDelta": -5
}

# Push event to blockchain
tx_hash_hex = None
receipt = None
try:
    if account:
        nonce = web3.eth.get_transaction_count(account.address)
        gas_price = web3.to_wei("5", "gwei")
        tx = contract.functions.addLog(
            event["eventHash"],
            event["anomalyType"],
            event["trustDelta"]
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": gas_price
        })

        signed_tx = account.sign_transaction(tx)
        # Correct attribute name in web3.py v6
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Event pushed to blockchain! TxHash: {tx_hash.hex()}")

        tx_hash_hex = tx_hash.hex()
    else:
        raise Exception("No PRIVATE_KEY provided")

except Exception as e:
    print(f"❌ Blockchain push failed, stored locally: {e}")
    tx_hash_hex = "LOCAL_" + event["eventHash"][:8]

# Store locally
local_entry = {
    "blockNumber": 0 if not receipt else receipt.blockNumber,
    "transactionHash": tx_hash_hex,
    "eventHash": event["eventHash"],
    "anomalyType": event["anomalyType"],
    "trustDelta": event["trustDelta"],
    "timestamp": datetime.utcnow().isoformat()
}

existing_logs = []
if os.path.exists(LOCAL_LOG_FILE):
    try:
        with open(LOCAL_LOG_FILE, "r") as f:
            existing_logs = json.load(f)
    except Exception:
        existing_logs = []

existing_logs.append(local_entry)

with open(LOCAL_LOG_FILE, "w") as f:
    json.dump(existing_logs, f, indent=2)

print(f"✅ Event stored locally: {tx_hash_hex}")

# Print last 5 logs
print(f"📜 Last 5 logs: {existing_logs[-5:]}")
