import requests

url = "https://eth-sepolia.g.alchemy.com/v2/kpTHq2-Woc1CVRev6shY2"

payload = {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "eth_sendRawTransaction",
    "params": ["0x9e63085271890a141297039b3b711913699f1ee4db1acb667ad7ce304772036b"]
}
headers = {
    "accept": "application/json",
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)