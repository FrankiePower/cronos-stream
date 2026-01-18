
import time
import httpx
from typing import List, Dict, Any
from eth_account import Account
from eth_account.messages import encode_typed_data
from hexbytes import HexBytes
from web3 import Web3

# Hardcoded for demo - in production this would come from env or discovery
CONTRACT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
CHAIN_ID = 31337

class ChannelManager:
    """
    Manages payment channel state and signs EIP-712 vouchers.
    """
    def __init__(self, private_key: str, channel_id: str, owner: str):
        self._private_key = private_key
        self._account = Account.from_key(private_key)
        
        self.channel_id = channel_id
        self.owner = owner
        self.contract_address = CONTRACT_ADDRESS
        self.chain_id = CHAIN_ID
        
        # State tracking
        self.sequence_number = 0
        self.cumulative_amounts: Dict[str, int] = {} # recipient -> total_amount

    async def ensure_channel(self, sequencer_url: str, initial_balance: str, expiry: int):
        """
        Ensures the channel is seeded on the sequencer.
        """
        async with httpx.AsyncClient() as client:
            # Check if exists
            try:
                res = await client.get(f"{sequencer_url}/channel/{self.channel_id}")
                if res.status_code == 200:
                    data = res.json()
                    print(f"Channel {self.channel_id} exists. Seq: {data.get('sequenceNumber')}")
                    # In a real app we would sync sequence number here
                    self.sequence_number = data.get('sequenceNumber', 0)
                    return
            except Exception as e:
                print(f"Error checking channel: {e}")

            # Seed if not found
            print(f"Seeding channel {self.channel_id}...")
            payload = {
                "channelId": self.channel_id,
                "owner": self.owner,
                "balance": initial_balance,
                "expiryTimestamp": expiry
            }
            res = await client.post(f"{sequencer_url}/channel/seed", json=payload)
            if res.status_code != 200:
                print(f"Failed to seed channel: {res.text}")
                raise Exception(f"Failed to seed channel: {res.text}")
            print("Channel seeded successfully.")

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
        # (In a real implementation we might support multiple recipients per voucher,
        # here we just list all active recipients with their updated totals)
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
        # Use encode_typed_data with full_message matching the EIP-712 dict
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
