# web3_utils.py
# Enhanced Web3 helper with proper error handling, authentication, and fallback logic
# Expects env vars: INFURA_SEPOLIA_URL, DEMO_PRIVATE_KEY, DEMO_ACCOUNT, CONTRACT_ADDR

import os
import json
import time
from typing import Optional, Dict,List
from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import TransactionNotFound, BlockNotFound
import requests

# Load environment variables
load_dotenv()

# Configuration
INFURA_URL = os.getenv("INFURA_SEPOLIA_URL")
PRIVATE_KEY = os.getenv("DEMO_PRIVATE_KEY") 
ACCOUNT = os.getenv("DEMO_ACCOUNT")
CONTRACT_ADDR = os.getenv("CONTRACT_ADDR")
ABI_PATH = os.path.join(os.path.dirname(__file__), "..", "MILBASTERLog_abi.json")

# Fallback RPC URLs for Sepolia testnet
FALLBACK_RPCS = [
    "https://rpc.sepolia.org",
    "https://sepolia.gateway.tenderly.co",
    "https://ethereum-sepolia.blockpi.network/v1/rpc/public",
    "https://sepolia.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161"  # Public Infura endpoint
]

class Web3Manager:
    def __init__(self):
        self.w3 = None
        self.contract = None
        self.is_connected = False
        self.current_rpc = None
        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize Web3 connection with fallback logic"""

        # Try primary Infura URL first if configured
        if INFURA_URL:
            try:
                self.w3 = Web3(Web3.HTTPProvider(INFURA_URL, request_kwargs={'timeout': 10}))
                if self.w3.is_connected():
                    self.current_rpc = INFURA_URL
                    self.is_connected = True
                    print(f"✅ Connected to primary RPC: {INFURA_URL[:50]}...")
                    self._load_contract()
                    return
                else:
                    print(f"⚠️ Primary RPC not responding: {INFURA_URL[:50]}...")
            except Exception as e:
                print(f"❌ Primary RPC failed: {str(e)[:100]}...")

        # Try fallback RPCs
        for rpc_url in FALLBACK_RPCS:
            try:
                print(f"🔄 Trying fallback RPC: {rpc_url[:50]}...")
                self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                if self.w3.is_connected():
                    self.current_rpc = rpc_url
                    self.is_connected = True
                    print(f"✅ Connected to fallback RPC: {rpc_url[:50]}...")
                    self._load_contract()
                    return
            except Exception as e:
                print(f"❌ Fallback RPC failed {rpc_url[:30]}...: {str(e)[:50]}...")
                continue

        # No connection established
        self.is_connected = False
        print("❌ No RPC connection established. Blockchain logging will be disabled.")

    def _load_contract(self):
        """Load smart contract ABI and initialize contract instance"""
        if not CONTRACT_ADDR:
            print("⚠️ CONTRACT_ADDR not set. Smart contract calls will fail.")
            return

        # Load ABI
        if os.path.exists(ABI_PATH):
            try:
                with open(ABI_PATH, "r") as f:
                    abi = json.load(f)
                print(f"✅ Loaded contract ABI from {ABI_PATH}")
            except Exception as e:
                print(f"❌ Failed to load ABI: {e}")
                abi = self._get_minimal_abi()
        else:
            print("⚠️ ABI file not found, using minimal ABI")
            abi = self._get_minimal_abi()

        try:
            self.contract = self.w3.eth.contract(address=CONTRACT_ADDR, abi=abi)
            print(f"✅ Contract initialized at {CONTRACT_ADDR}")
        except Exception as e:
            print(f"❌ Contract initialization failed: {e}")

    def _get_minimal_abi(self):
        """Return minimal ABI for basic contract interaction"""
        return [
            {
                "inputs": [
                    {"internalType": "string", "name": "eventHash", "type": "string"},
                    {"internalType": "string", "name": "anomalyType", "type": "string"}, 
                    {"internalType": "int256", "name": "trustDelta", "type": "int256"}
                ],
                "name": "addLog",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "string", "name": "eventHash", "type": "string"}
                ],
                "name": "storeEvent", 
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
    
    def check_connection(self) -> bool:
        """Check if Web3 connection is still active"""
        if not self.w3 or not self.is_connected:
            return False

        try:
            # Simple connectivity test
            self.w3.eth.block_number
            return True
        except Exception:
            print("❌ Connection lost, attempting reconnection...")
            self.is_connected = False
            self._initialize_connection()
            return self.is_connected

    def get_gas_price(self) -> int:
        """Get current gas price with fallback"""
        try:
            if self.check_connection():
                return self.w3.eth.gas_price
            else:
                return self.w3.to_wei("20", "gwei")  # Fallback gas price
        except Exception:
            return self.w3.to_wei("20", "gwei")

    def estimate_gas(self, transaction) -> int:
        """Estimate gas for transaction with fallback"""
        try:
            if self.check_connection():
                return self.w3.eth.estimate_gas(transaction)
            else:
                return 200000  # Conservative fallback
        except Exception:
            return 200000

# Global Web3 manager instance
web3_manager = Web3Manager()


def verify_transaction(tx_hash: str, timeout: int = 60) -> Dict:
    """
    Verify transaction was mined successfully

    Args:
        tx_hash: Transaction hash to verify
        timeout: Timeout in seconds

    Returns:
        Transaction receipt dict or error info
    """
    if not web3_manager.check_connection():
        return {"error": "No blockchain connection"}

    try:
        w3 = web3_manager.w3
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)

        return {
            "success": True,
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "status": receipt.status
        }

    except TransactionNotFound:
        return {"error": "Transaction not found"}
    except Exception as e:
        return {"error": str(e)}

def get_blockchain_status() -> Dict:
    """Get current blockchain connection status"""
    return {
        "connected": web3_manager.is_connected,
        "current_rpc": web3_manager.current_rpc,
        "contract_address": CONTRACT_ADDR,
        "account": ACCOUNT,
        "block_number": web3_manager.w3.eth.block_number if web3_manager.is_connected else None
    }
    # At the top, add a simple local cache
local_log_cache = []

# Modify push_event_to_chain() at the end, add this:

def push_event_to_chain(event_hash_hex: str, anomaly_type: int = 1, trust_delta: int = 0) -> Optional[str]:
    """
    Push event hash to blockchain with comprehensive error handling.
    Always store in local cache.
    """
    tx_hash_hex = None

    if web3_manager.is_connected and all([PRIVATE_KEY, ACCOUNT, CONTRACT_ADDR]):
        try:
            w3 = web3_manager.w3
            contract = web3_manager.contract
            if contract:
                nonce = w3.eth.get_transaction_count(ACCOUNT)
                gas_price = web3_manager.get_gas_price()
                # Try addLog
                try:
                    txn = contract.functions.addLog(
                        event_hash_hex,
                        str(anomaly_type),
                        int(trust_delta)
                    ).build_transaction({
                        "chainId": 11155111,
                        "gas": 250000,
                        "gasPrice": gas_price,
                        "nonce": nonce,
                        "from": ACCOUNT
                    })
                except:
                    # fallback storeEvent
                    txn = contract.functions.storeEvent(event_hash_hex).build_transaction({
                        "chainId": 11155111,
                        "gas": 200000,
                        "gasPrice": gas_price,
                        "nonce": nonce,
                        "from": ACCOUNT
                    })

                signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                tx_hash_hex = w3.to_hex(tx_hash)

        except Exception as e:
            print(f"❌ Blockchain push failed, stored locally: {str(e)[:100]}...")

    # Always store in local cache
    log_entry = {
        "blockNumber": 0 if not tx_hash_hex else None,
        "transactionHash": tx_hash_hex if tx_hash_hex else "LOCAL_" + event_hash_hex[:8],
        "eventHash": event_hash_hex,
        "anomalyType": anomaly_type,
        "trustDelta": trust_delta
    }
    local_log_cache.append(log_entry)
    print(f"✅ Event stored locally: {log_entry['transactionHash']}")
    return tx_hash_hex

# Modify get_logs_from_chain to include local logs:
def get_logs_from_chain(from_block: int = 0, to_block: str = "latest") -> List[Dict]:
    """
    Return logs from blockchain + local cache
    """
    chain_logs = []
    if web3_manager.is_connected:
        try:
            contract = web3_manager.contract
            if contract:
                event_filter = contract.events.LogAdded.create_filter(
                    fromBlock=from_block, toBlock=to_block
                )
                chain_logs = [
                    {
                        "blockNumber": log.blockNumber,
                        "transactionHash": log.transactionHash.hex(),
                        "eventHash": log.args.get("eventHash"),
                        "anomalyType": log.args.get("anomalyType"),
                        "trustDelta": log.args.get("trustDelta")
                    }
                    for log in event_filter.get_all_entries()
                ]
        except:
            pass

    # Merge local logs
    return chain_logs + local_log_cache

# Test connection on import
if __name__ == "__main__":
    status = get_blockchain_status()
    print("Blockchain Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")