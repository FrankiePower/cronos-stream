import os
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import json

load_dotenv("a2a/a2a-service/.env")
load_dotenv("sequencer/.env") # For RPC

# Config
RPC_URL = "https://evm-t3.cronos.org/" 
PRIVATE_KEY = os.getenv("X402_AGENT_PRIVATE_KEY")
CHANNEL_MANAGER_ADDRESS = "0xE118E04431853e9df5390E1AACF36dEF6A7a0254"

# Load Channel ID
with open("a2a/a2a-service/channel_state.json", "r") as f:
    state = json.load(f)
    CHANNEL_ID = state["channelId"]

# Contract ABI (Minimal)
ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "channelId", "type": "bytes32"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "expiry", "type": "uint256"}
        ],
        "name": "createChannel",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = Account.from_key(PRIVATE_KEY)
    
    print(f"Opening Channel {CHANNEL_ID} on-chain...")
    print(f"From: {account.address}")
    
    contract = w3.eth.contract(address=CHANNEL_MANAGER_ADDRESS, abi=ABI)
    
    # 0.01 TCRO
    amount = w3.to_wei(0.01, 'ether')
    expiry = int(time.time()) + 3600 * 24 # 24 hours
    
    tx = contract.functions.createChannel(
        CHANNEL_ID,
        amount,
        expiry
    ).build_transaction({
        'from': account.address,
        'value': amount, # Send the TCRO
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price
    })
    
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    
    print(f"Transaction sent! Hash: {w3.to_hex(tx_hash)}")
    print("Waiting for receipt...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        print("Channel Opened Successfully! 🟢")
    else:
        print("Transaction Failed! 🔴")

if __name__ == "__main__":
    main()
