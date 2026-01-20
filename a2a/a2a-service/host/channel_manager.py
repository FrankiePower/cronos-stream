
import time
import httpx
from typing import List, Dict, Any
from eth_account import Account
from eth_account.messages import encode_typed_data
from hexbytes import HexBytes
from web3 import Web3

import os

# Hardcoded for demo - in production this would come from env or discovery
CHANNEL_MANAGER_ADDRESS = os.getenv("CHANNEL_MANAGER_ADDRESS", "0xE118E04431853e9df5390E1AACF36dEF6A7a0254")
CHAIN_ID = int(os.getenv("CHAIN_ID", "338"))
RPC_URL = os.getenv("RPC_URL", "https://evm-t3.cronos.org/")

# ABIs
ERC20_ABI = [
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

CHANNEL_ABI = [
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "expiryTime", "type": "uint256"}, {"name": "amount", "type": "uint256"}], "name": "getChannelId", "outputs": [{"name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "amount", "type": "uint256"}, {"name": "expiryTime", "type": "uint256"}, {"name": "signatureTimestamp", "type": "uint256"}, {"name": "userSignature", "type": "bytes"}], "name": "openChannel", "outputs": [{"name": "channelId", "type": "bytes32"}], "stateMutability": "nonpayable", "type": "function"}
]

class ChannelManager:
    """
    Manages payment channel state, on-chain creation, and signs EIP-712 vouchers.
    """
    def __init__(self, private_key: str, channel_id: str, owner: str):
        self._private_key = private_key
        self._account = Account.from_key(private_key)
        
        # If channel_id is not provided, we will calculate it later
        self.channel_id = channel_id
        self.owner = owner
        self.contract_address = CHANNEL_MANAGER_ADDRESS
        self.chain_id = CHAIN_ID
        
        # Web3 Setup
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        # devUSDC Address on Cronos Testnet
        self.usdc_address = "0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0" 
        
        # State tracking
        self.sequence_number = 0
        self.cumulative_amounts: Dict[str, int] = {} # recipient -> total_amount

    async def ensure_channel(self, sequencer_url: str, initial_balance: str, expiry: int):
        """
        Ensures the channel exists on-chain and is seeded on the sequencer.
        If not on-chain, it executes Approval and OpenChannel transactions.
        """
        amount_wei = int(initial_balance)
        
        # 1. Check Sequencer First (Fast Path)
        if self.channel_id:
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.get(f"{sequencer_url}/channel/{self.channel_id}")
                    if res.status_code == 200:
                        data = res.json()
                        self.sequence_number = data.get('sequenceNumber', 0)
                        # Sync balances...
                        recipients = data.get('recipients', [])
                        for r in recipients:
                            r_addr = r.get('recipientAddress')
                            r_bal = int(r.get('balance', '0'))
                            if r_addr:
                                 try:
                                     r_addr = Web3.to_checksum_address(r_addr)
                                     self.cumulative_amounts[r_addr] = r_bal
                                 except Exception:
                                     pass
                        print(f"Channel {self.channel_id} found on sequencer. Synced.")
                        return
                except Exception as e:
                    print(f"Sequencer check failed (will try on-chain): {e}")

        # 2. Calculate Channel ID if needed (or verify existing)
        contract = self.w3.eth.contract(address=self.contract_address, abi=CHANNEL_ABI)
        
        # We need to calculate the ID the contract *would* generate
        # Note: In a real app, we might check if a channel already exists for this owner/expiry,
        # but here we assume we are creating a new specific one.
        predicted_id = contract.functions.getChannelId(
            self.owner,
            expiry,
            amount_wei
        ).call()
        
        self.channel_id = '0x' + predicted_id.hex() # Ensure hex string format
        print(f"Target Channel ID: {self.channel_id}")

        # 3. Check On-Chain Requirements (USDC)
        usdc = self.w3.eth.contract(address=self.usdc_address, abi=ERC20_ABI)
        
        # Check Allowance
        allowance = usdc.functions.allowance(self.owner, self.contract_address).call()
        if allowance < amount_wei:
            print(f"Approving USDC spend (Current: {allowance}, Need: {amount_wei})...")
            approve_tx = usdc.functions.approve(self.contract_address, amount_wei).build_transaction({
                'from': self.owner,
                'nonce': self.w3.eth.get_transaction_count(self.owner),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, self._private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Approve TX Sent: {self.w3.to_hex(tx_hash)}")
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print("USDC Approved.")

        # 4. Open Channel On-Chain
        # We need a self-signature for the openChannel call as proof of authority
        # This matches the reference implementation `signChannelUpdate` with sequence 0
        timestamp = int(time.time())
        signature = self._sign_open_channel(timestamp)
        
        try:
            print(f"Opening Channel on-chain...")
            open_tx = contract.functions.openChannel(
                amount_wei,
                expiry,
                timestamp,
                HexBytes(signature)
            ).build_transaction({
                'from': self.owner,
                'nonce': self.w3.eth.get_transaction_count(self.owner),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(open_tx, self._private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Open Channel TX Sent: {self.w3.to_hex(tx_hash)}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status != 1:
                raise Exception(f"Open Channel Transaction Failed! Hash: {self.w3.to_hex(tx_hash)}")
            print("Channel Opened On-Chain successfully.")
        except Exception as e:
            # STRICT MODE: If it fails, we CRASH. No fake payments.
            print(f"CRITICAL: Failed to open channel on-chain: {e}")
            raise e

        # 5. Seed Sequencer (Only reachable if on-chain succeeded)
        async with httpx.AsyncClient() as client:
            print(f"Seeding sequencer {self.channel_id}...")
            payload = {
                "channelId": self.channel_id,
                "owner": self.owner,
                "balance": str(amount_wei),
                "expiryTimestamp": expiry
            }
            res = await client.post(f"{sequencer_url}/channel/seed", json=payload)
            if res.status_code != 200:
                print(f"Failed to seed channel: {res.text}")
                # Don't raise here, we want to try using it anyway
            print("Channel seeded in sequencer.")

    def _sign_open_channel(self, timestamp: int) -> str:
        # Construct EIP-712 payload for initial state (seq 0)
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
                "chainId": self.chain_id,
                "verifyingContract": self.contract_address
            },
            "primaryType": "ChannelData",
            "message": {
                "channelId": HexBytes(self.channel_id),
                "sequenceNumber": 0,
                "timestamp": timestamp,
                "recipients": [],
                "amounts": []
            }
        }
        encoded_msg = encode_typed_data(full_message=data)
        signed_msg = self._account.sign_message(encoded_msg)
        return signed_msg.signature.hex()

    def create_voucher(self, recipient: str, amount_wei: int) -> Dict[str, Any]:
        """
        Creates a signed voucher for a payment.
        Increments sequence number and updates cumulative balance.
        """
        self.sequence_number += 1
        timestamp = int(time.time())
        
        # Update cumulative balance for this recipient
        current_amount = self.cumulative_amounts.get(recipient, 0)
        new_total = current_amount + amount_wei
        self.cumulative_amounts[recipient] = new_total
        
        # Flatten recipients and amounts for the struct
        recipients_list = list(self.cumulative_amounts.keys())
        amounts_list = [self.cumulative_amounts[r] for r in recipients_list]
        
        # 1. Construct EIP-712 payload
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
                "chainId": self.chain_id,
                "verifyingContract": self.contract_address
            },
            "primaryType": "ChannelData",
            "message": {
                "channelId": HexBytes(self.channel_id),
                "sequenceNumber": self.sequence_number,
                "timestamp": timestamp,
                "recipients": recipients_list,
                "amounts": amounts_list
            }
        }
        
        # 2. Sign
        encoded_msg = encode_typed_data(full_message=data)
        signed_msg = self._account.sign_message(encoded_msg)
        signature = signed_msg.signature.hex()
        
        # 3. Return payload for API
        return {
            "channelId": self.channel_id,
            "amount": str(amount_wei),        # Delta amount for this payment (info only)
            "receiver": recipient,
            "sequenceNumber": self.sequence_number,
            "timestamp": timestamp,
            "userSignature": signature,
            # Internal fields for debugging/tracking
            "totalAmount": str(new_total) 
        }

    def get_state(self):
        return {
            "channelId": self.channel_id,
            "sequenceNumber": self.sequence_number,
            "balances": self.cumulative_amounts
        }
