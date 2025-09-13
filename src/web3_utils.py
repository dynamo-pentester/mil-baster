# web3_placeholder.py
# Example of how to send an onchain log once you have Infura and private key configured.
# DO NOT put private keys into code for real deployment. For demo, use env vars or .env and keep secret.

import os
from web3 import Web3
import json

INFURA_URL = os.getenv("INFURA_SEPOLIA_URL")  # e.g., https://sepolia.infura.io/v3/...
PRIVATE_KEY = os.getenv("DEMO_PRIVATE_KEY")
ACCOUNT = os.getenv("DEMO_ACCOUNT")  # 0x...
CONTRACT_ADDR = os.getenv("CONTRACT_ADDR")
ABI_PATH = "MILBASTERLog_abi.json"

def init_web3():
    w3 = Web3(Web3.HTTPProvider(INFURA_URL))
    if not w3.is_connected():
        raise RuntimeError("web3 not connected")
    with open(ABI_PATH) as f:
        abi = json.load(f)
    contract = w3.eth.contract(address=CONTRACT_ADDR, abi=abi)
    return w3, contract

def push_event_to_chain(event_hash_hex, anomaly_type:int, trust_delta:int):
    w3, contract = init_web3()
    nonce = w3.eth.get_transaction_count(ACCOUNT)
    txn = contract.functions.addLog(event_hash_hex, str(anomaly_type), int(trust_delta)).build_transaction({
        "chainId": 11155111,  # Sepolia chain id (keep updated)
        "gas": 200000,
        "gasPrice": w3.to_wei("10", "gwei"),
        "nonce": nonce,
        "from": ACCOUNT
    })
    signed = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print("Pushed event, tx:", w3.to_hex(tx_hash))
    return w3.to_hex(tx_hash)
