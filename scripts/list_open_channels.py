import os
import json
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, "a2a", "a2a-service", ".env")
load_dotenv(env_path)

RPC_URL = "https://evm-t3.cronos.org/"
PRIVATE_KEY = os.getenv("X402_AGENT_PRIVATE_KEY")
STREAM_CHANNEL_ADDRESS = "0xE118E04431853e9df5390E1AACF36dEF6A7a0254"

# Minimal ABI for StreamChannel
STREAM_CHANNEL_ABI = [
    {"inputs": [{"name": "owner", "type": "address"}], "name": "getUserChannelLength", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "", "type": "address"}, {"name": "", "type": "uint256"}], "name": "userChannels", "outputs": [{"name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "", "type": "bytes32"}], "name": "channels", "outputs": [
        {"name": "owner", "type": "address"},
        {"name": "balance", "type": "uint256"},
        {"name": "expiryTime", "type": "uint256"},
        {"name": "sequenceNumber", "type": "uint256"}
    ], "stateMutability": "view", "type": "function"}
]

def main():
    if not PRIVATE_KEY:
        print("Error: X402_AGENT_PRIVATE_KEY not found in .env")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = Account.from_key(PRIVATE_KEY)
    user_address = account.address
    
    print(f"--- Checking Channels for {user_address} ---")
    print(f"Connecting to RPC: {RPC_URL}...")
    
    contract = w3.eth.contract(address=STREAM_CHANNEL_ADDRESS, abi=STREAM_CHANNEL_ABI)
    
    # Check Contract's Total USDC Balance
    usdc_abi = [{"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
                {"inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}]
    usdc_address = "0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0"
    usdc = w3.eth.contract(address=usdc_address, abi=usdc_abi)
    
    print("Checking Contract Balances...")
    contract_bal_raw = usdc.functions.balanceOf(STREAM_CHANNEL_ADDRESS).call()
    contract_bal = contract_bal_raw / 1e6
    print(f"🏦 Contract Total USDC: {contract_bal} USDC")

    try:
        print("Fetching user channel length...")
        count = contract.functions.getUserChannelLength(user_address).call()
        print(f"Total Channels for User: {count}")
        
        current_time = int(time.time())

        print(f"\n--- Channel List ({count}) ---")
        for i in range(count):
            channel_id = contract.functions.userChannels(user_address, i).call()
            channel_data = contract.functions.channels(channel_id).call()
            
            balance = channel_data[1]
            expiry = channel_data[2]
            sequence = channel_data[3]
            balance_fmt = balance / 1e6 
            
            status = "OPEN" if balance > 0 else "CLOSED/EMPTY"
            if balance > 0 and current_time > expiry:
                status = "EXPIRED (Funds Locked)"
            
            print(f"[{i}] {status} | ID: {channel_id.hex()[:10]}... | bal: {balance_fmt} | seq: {sequence}")
            
    except Exception as e:
        print(f"Error querying contract: {e}")

if __name__ == "__main__":
    main()
