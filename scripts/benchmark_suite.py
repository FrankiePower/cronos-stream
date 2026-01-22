import os
import time
import sys
import asyncio
import httpx
import secrets
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_typed_data
from hexbytes import HexBytes

# Add parent dir to path to import ChannelManager if needed, 
# but for benchmark isolation, we'll implement a standalone optimized client.

from dotenv import load_dotenv

# Load env from a2a-service
load_dotenv("a2a/a2a-service/.env")

RPC_URL = "https://evm-t3.cronos.org/"
SEQUENCER_URL = "http://localhost:4001"
# We target the Resource Service's voucher endpoint directly to test the full flow
SERVICE_URL = "http://localhost:8787/api/pay-voucher"
CHAIN_ID = 338
CHANNEL_MANAGER_ADDRESS = "0xE118E04431853e9df5390E1AACF36dEF6A7a0254"

# Private key for benchmarking (should be loaded from env)
PRIVATE_KEY = os.getenv("X402_AGENT_PRIVATE_KEY")

class BenchmarkClient:
    def __init__(self, private_key):
        self.account = Account.from_key(private_key)
        self.channel_id = None
        self.sequence_number = 0
        self.contract_address = CHANNEL_MANAGER_ADDRESS
        self.chain_id = CHAIN_ID

    async def sync_state(self):
        # Fetch current state from sequencer
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{SEQUENCER_URL}/channel/{self.channel_id}")
            if res.status_code == 200:
                data = res.json()
                self.sequence_number = int(data["sequenceNumber"])
                
                # Parse recipients
                self.balances = {} # address -> int
                for r in data["recipients"]:
                    addr = r["recipientAddress"].lower()
                    amt = int(r["balance"]) # handle huge ints
                    self.balances[addr] = amt
                    
                print(f"Synced State: Seq={self.sequence_number}, Balances={self.balances}")
            else:
                print(f"Failed to sync sequence: {res.text}")
                self.balances = {}

    def get_voucher(self, sequence_number):
        timestamp = int(time.time())
        amount_to_pay = 1
        merchant = "0x2aece1250b1774f3fc462424475705cf4cf539de" # lowercase
        
        # Clone current balances to simulate next state
        next_balances = self.balances.copy()
        current_bal = next_balances.get(merchant, 0)
        next_balances[merchant] = current_bal + amount_to_pay
        
        # Prepare arrays for EIP-712 (Consistently ordered? Usually order of insertion or just list)
        # Ref impl uses the list from the channel view. 
        # We need to construct lists matching what Sequencer produces.
        # Sequencer appends new recipients. Updates existing ones in place.
        # So order matters!
        # We will assume single recipient for benchmark to keep it simple, 
        # OR we rely on the fact that we synced from server which gave us a list.
        # But we simplified locally to a Dict. A Dict loses order (pre-3.7).
        # We should store as list.
        
        # Simplified: We know we only pay Merchant in this bench.
        # So recipients is always [Merchant] or [] if new.
        recipients = [merchant]
        amounts = [next_balances[merchant]]

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
                "sequenceNumber": sequence_number,
                "timestamp": timestamp,
                "recipients": recipients,
                "amounts": amounts     
            }
        }
        
        encoded = encode_typed_data(full_message=data)
        signed = self.account.sign_message(encoded)
        
        # Return LOCAL tracking info too so the caller can update state on success
        return {
            "payload": {
                "channelId": self.channel_id,
                "amount": str(amount_to_pay),
                "receiver": merchant,
                "sequenceNumber": sequence_number,
                "timestamp": timestamp,
                "userSignature": signed.signature.hex(),
                "paymentId": "bench-payment-id"
            },
            "new_balances": next_balances
        }



    async def setup_channel(self):
        # reuse a channel or make a random one for bench
        self.channel_id = "0x" + secrets.token_hex(32)
        print(f"Using Benchmark Channel: {self.channel_id}")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "channelId": self.channel_id,
                "owner": self.account.address,
                "balance": "1000000000",
                "expiryTimestamp": int(time.time()) + 3600
            }
            res = await client.post(f"{SEQUENCER_URL}/channel/seed", json=payload)
            if res.status_code != 200:
                print(f"Seed failed: {res.text}")

    async def run_live_signing(self, duration_sec):
        print(f"\n--- Live Signing Benchmark ({duration_sec}s) ---")
        end_time = time.time() + duration_sec
        count = 0
        success_count = 0
        
        # Sync first
        await self.sync_state()
        current_seq = self.sequence_number

        async with httpx.AsyncClient() as client:
            while time.time() < end_time:
                next_seq = current_seq + 1
                result = self.get_voucher(next_seq)
                try:
                    res = await client.post(SERVICE_URL, json=result["payload"])
                    if res.status_code == 200:
                        success_count += 1
                        current_seq = next_seq
                        self.balances = result["new_balances"] # Update state
                    else:
                        print(f"Req failed: {res.status_code} - {res.text}")
                    count += 1
                except Exception as e:
                    print(f"Err: {e}")
        
        self.sequence_number = current_seq
        print(f"Completed {success_count}/{count} successful reqs in {duration_sec}s")
        print(f"Throughput: {success_count / duration_sec:.2f} req/s")

    async def run_presigned(self, count):
        print(f"\n--- Pre-Signed Benchmark ({count} reqs) ---")
        await self.sync_state()
        start_seq = self.sequence_number + 1
        
        results = []
        print("Generating signatures...")
        t0 = time.time()
        # We must generate sequentially because each depends on previous balance
        # For the generation phase, we assume success for each step
        temp_balances = self.balances.copy()
        
        # We need to temporarily mock the self.balances to generate the chain
        # Actually, get_voucher reads self.balances. 
        # But get_voucher does NOT update self.balances (it returns new_balances).
        # So I must update self.balances in the generation loop locally?
        # Yes.
        
        original_balances = self.balances.copy()
        
        for i in range(count):
            res = self.get_voucher(start_seq + i)
            results.append(res)
            self.balances = res["new_balances"] # Assume success for generation
            
        gen_time = time.time() - t0
        print(f"Generation took {gen_time:.2f}s ({count/gen_time:.0f} sig/s)")
        
        # Revert self.balances to start state before sending?
        # Actually, if we send them all, the state WILL reach the end state.
        # But if the first one fails, we are doomed anyway.
        # We leave self.balances at the end state, assuming all will pass.
        
        print("Sending requests...")
        t_start = time.time()
        success_count = 0
        async with httpx.AsyncClient() as client:
            for res in results:
                resp = await client.post(SERVICE_URL, json=res["payload"])
                if resp.status_code == 200:
                    success_count += 1
                else:
                    print(f"Fail: {resp.status_code} - {resp.text}")
                    break 
                
        elapsed = time.time() - t_start
        print(f"Sent {success_count} reqs in {elapsed:.2f}s")
        print(f"Throughput: {success_count / elapsed:.2f} req/s")

    def close_channel(self):
        print(f"Closing Benchmark Channel {self.channel_id}...")
        
        # 1. Prepare final state
        timestamp = int(time.time())
        recipients_list = list(self.balances.keys())
        amounts_list = [self.balances[r] for r in recipients_list]
        
        # 2. Sign "I agree to close with this state"
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
        
        encoded_msg = encode_typed_data(full_message=data)
        signed_msg = self.account.sign_message(encoded_msg)
        # user_signature = signed_msg.signature.hex() # Not needed if just triggering endpoints that don't verify strict user sig yet?
        
        # 3. Request Sequencer to Finalize (Mutual Close)
        import requests
        try:
            res = requests.post(f"{SEQUENCER_URL}/channel/finalize", json={"channelId": self.channel_id})
            if res.status_code == 200:
                print(f"✅ Sequencer closure triggered! Hash: {res.json().get('transactionHash')}")
            else:
                print(f"❌ Sequencer refused closure: {res.text}")
        except Exception as e:
            print(f"❌ Failed to contact sequencer for closure: {e}")

async def main():
    if not PRIVATE_KEY:
        print("Error: X402_AGENT_PRIVATE_KEY is missing.")
        return

    client = BenchmarkClient(PRIVATE_KEY)
    
    try:
        await client.setup_channel()
        
        # 1. Live Signing (10s)
        await client.run_live_signing(10)
        
        # 2. Pre-Signed (1000 reqs)
        await client.run_presigned(1000)
        
    finally:
        if client.channel_id:
            client.close_channel()

if __name__ == "__main__":
    asyncio.run(main())
