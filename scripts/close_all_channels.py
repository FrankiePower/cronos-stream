import os
import time
import requests
import json
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
SEQUENCER_URL = "http://localhost:4001"

SEQUENCER_PRIVATE_KEY_VAL = "006be97812c4c96d97f664c9b846f92e92957a3029c7d02957e1c242062ff7a2"

STREAM_CHANNEL_ABI = [
    {"inputs": [{"name": "owner", "type": "address"}], "name": "getUserChannelLength", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "", "type": "address"}, {"name": "", "type": "uint256"}], "name": "userChannels", "outputs": [{"name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "", "type": "bytes32"}], "name": "channels", "outputs": [
        {"name": "owner", "type": "address"},
        {"name": "balance", "type": "uint256"},
        {"name": "expiryTime", "type": "uint256"},
        {"name": "sequenceNumber", "type": "uint256"}
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "channelId", "type": "bytes32"}], "name": "closeAfterExpiryByAnyone", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "channelId", "type": "bytes32"}, {"name": "sequenceNumber", "type": "uint256"}, {"name": "timestamp", "type": "uint256"}, {"name": "recipients", "type": "address[]"}, {"name": "amounts", "type": "uint256[]"}, {"name": "userSignature", "type": "bytes"}], "name": "finalCloseBySequencer", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

from eth_account.messages import encode_typed_data
from hexbytes import HexBytes

def sign_channel_state(w3, channel_id, sequence, timestamp, recipients, amounts, private_key):
    data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"}
            ],
            "ChannelData": [
                {"name": "channelId", "type": "bytes32"},
                {"name": "sequenceNumber", "type": "uint256"},
                {"name": "timestamp", "type": "uint256"},
                {"name": "recipients", "type": "address[]"},
                {"name": "amounts", "type": "uint256[]"}
            ]
        },
        "domain": {
            "name": "StreamChannel",
            "version": "1",
            "chainId": 338,
            "verifyingContract": STREAM_CHANNEL_ADDRESS
        },
        "primaryType": "ChannelData",
        "message": {
            "channelId": HexBytes(channel_id),
            "sequenceNumber": sequence,
            "timestamp": timestamp,
            "recipients": recipients,
            "amounts": amounts
        }
    }
    
    encoded_msg = encode_typed_data(full_message=data)
    account = Account.from_key(private_key)
    signed = account.sign_message(encoded_msg)
    return signed.signature

def close_via_dual_key(w3, contract, channel_id, sequence, balance):
    print(f"  Attempting Dual-Key Mutual Close...")
    
    # 1. Prepare State (Return everything to owner, owe 0 to others)
    # Since we don't know who the recipients were, we assume we want to just close it.
    # If we set recipients=[], amounts=[], it means we owe nothing.
    # The contract will return remaining balance to owner.
    # Sequence must be >= current.
    
    timestamp = int(time.time())
    recipients = []
    amounts = []
    
    # 2. User Signs "I agree to this state"
    user_sig = sign_channel_state(w3, channel_id, sequence, timestamp, recipients, amounts, PRIVATE_KEY)
    
    # 3. Sequencer Submits "finalCloseBySequencer"
    sequencer_account = Account.from_key(SEQUENCER_PRIVATE_KEY_VAL)
    
    try:
        tx = contract.functions.finalCloseBySequencer(
            channel_id,
            sequence,
            timestamp,
            recipients,
            amounts,
            user_sig
        ).build_transaction({
            'from': sequencer_account.address,
            'nonce': w3.eth.get_transaction_count(sequencer_account.address),
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, SEQUENCER_PRIVATE_KEY_VAL)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"  ✅ Sequencer close tx sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("  ✅ Transaction confirmed!")
            return True
        else:
            print(f"  ❌ Transaction reverted! (Gas used: {receipt.gasUsed})")
            return False
            
    except Exception as e:
        print(f"  ❌ Sequencer submit failed: {e}")
        return False

def main():
    if not PRIVATE_KEY:
        print("Error: X402_AGENT_PRIVATE_KEY not found")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = Account.from_key(PRIVATE_KEY)
    user_address = account.address
    
    print(f"--- Closing All Channels for {user_address} ---")
    
    contract = w3.eth.contract(address=STREAM_CHANNEL_ADDRESS, abi=STREAM_CHANNEL_ABI)
    
    count = contract.functions.getUserChannelLength(user_address).call()
    print(f"Found {count} total channels (history). Scanning for active ones...")
    
    current_time = int(time.time())
    
    channel_ids = []
    for i in range(count):
        channel_ids.append(contract.functions.userChannels(user_address, i).call())

    unique_ids = list(set(channel_ids))
    
    for channel_id in unique_ids:
        # Re-fetch data 
        c = contract.functions.channels(channel_id).call()
        balance = c[1]
        expiry = c[2]
        sequence = c[3] # current sequence
        
        if balance > 0:
            channel_hex = channel_id.hex()
            print(f"\nProcessing Channel: {channel_hex[:10]}... (Bal: {balance/1e6} USDC)")
            
            if current_time > expiry:
                print("  Status: EXPIRED")
                close_via_contract(w3, contract, account, channel_id)
            else:
                print("  Status: ACTIVE")
                # Try dual key close
                close_via_dual_key(w3, contract, channel_id, sequence, balance)

if __name__ == "__main__":
    main()
