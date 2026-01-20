import os
import requests
import json
import time
from web3 import Web3
from dotenv import load_dotenv

load_dotenv("a2a/a2a-service/.env")

RPC_URL = "https://evm-t3.cronos.org/"
USDC_ADDRESS = "0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0"
MERCHANT_ADDRESS = "0x2AeCE1250b1774f3Fc462424475705cF4cF539dE"
SEQUENCER_URL = "http://localhost:4001"

ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}
]

def get_balance(w3, contract, address):
    decimals = contract.functions.decimals().call()
    raw = contract.functions.balanceOf(address).call()
    return raw / (10 ** decimals), raw

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    usdc = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
    
    # 1. Check Initial Balance
    print(f"Checking Merchant Balance ({MERCHANT_ADDRESS})...")
    bal_before, raw_before = get_balance(w3, usdc, MERCHANT_ADDRESS)
    print(f"💰 Balance Before: {bal_before} USDC (Raw: {raw_before})")
    
    # 2. Get Channel ID
    # TODO: Update this to match your active channel ID from the Agent logs or database
    channel_id = "0x6a99273cd613dcaa127d53981cbffc8f47c5b3ebacebf205c7cd310f48e1c0d3"
    
    print(f"Running Settlement for Channel: {channel_id}")
    
    # 3. Trigger Finalize
    print("Triggering Sequencer Finalization...")
    t0 = time.time()
    try:
        res = requests.post(f"{SEQUENCER_URL}/channel/finalize", json={"channelId": channel_id})
        if res.status_code != 200:
            print(f"❌ Finalize Failed: {res.text}")
            return
        
        data = res.json()
        tx_hash = data.get("transactionHash")
        print(f"✅ Finalize Request Success!")
        print(f"🔗 Transaction Hash: {tx_hash}")
        
    except Exception as e:
        print(f"❌ Error contacting sequencer: {e}")
        return

    # 4. Wait for Confirmation
    print("Waiting for transaction confirmation...")
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"✅ Transaction Confirmed! (Block: {receipt.blockNumber})")
        else:
            print("❌ Transaction Reverted on-chain!")
            return
    except Exception as e:
        print(f"❌ Error waiting for receipt: {e}")
        return
        
    # 5. Check Final Balance
    print("Checking New Balance...")
    bal_after, raw_after = get_balance(w3, usdc, MERCHANT_ADDRESS)
    print(f"💰 Balance After:  {bal_after} USDC (Raw: {raw_after})")
    
    diff = raw_after - raw_before
    if diff > 0:
        print(f"🎉 SUCCESS! Merchant received {diff} units.")
    else:
        print("⚠️ Warning: Balance did not increase (maybe paid to another recipient due to fees?).")

if __name__ == "__main__":
    main()
