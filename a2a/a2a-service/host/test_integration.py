
import asyncio
import os
import time
import httpx
from eth_account import Account
import secrets
from channel_manager import ChannelManager

# Configuration
X402_PRIVATE_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
RESOURCE_URL = "http://localhost:8787/api/data"
CHANNEL_ID = "0x" + secrets.token_hex(32)

async def main():
    print(f"--- Starting Integration Test ---")
    print(f"Resource: {RESOURCE_URL}")
    print(f"Wallet: {Account.from_key(X402_PRIVATE_KEY).address}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Request Protected Resource
        print("\n[1] Requesting protected resource...")
        res = await client.get(RESOURCE_URL)
        print(f"Status: {res.status_code}")
        
        if res.status_code == 200:
            print("Resource is already unlocked!")
            return

        if res.status_code != 402:
            print(f"Unexpected status: {res.text}")
            return

        # 2. Parse Challenge
        print("\n[2] Parsing 402 Challenge...")
        challenge = res.json()
        accepts_list = challenge.get("accepts", [])
        
        streaming_opt = next((a for a in accepts_list if a.get("scheme") == "streaming"), None)
        if not streaming_opt:
            print("No streaming scheme found in challenge!")
            print(challenge)
            return
            
        print("Found streaming scheme!")
        extra = streaming_opt.get("extra", {})
        payment_id = extra.get("paymentId")
        sequencer_url = extra.get("sequencerUrl")
        pay_to = streaming_opt.get("payTo")
        amount = int(streaming_opt.get("maxAmountRequired", "0"))
        
        print(f"Payment Details:\n - ID: {payment_id}\n - Sequencer: {sequencer_url}\n - Amount: {amount}\n - PayTo: {pay_to}")

        # 3. Setup Channel Manager
        print("\n[3] Setting up Channel Manager...")
        owner_acct = Account.from_key(X402_PRIVATE_KEY)
        cm = ChannelManager(X402_PRIVATE_KEY, CHANNEL_ID, owner_acct.address)
        
        # 4. Ensure Channel Exists
        print("\n[4] Ensuring Channel (Seeding)...")
        expiry = int(time.time()) + 31536000
        await cm.ensure_channel(sequencer_url, "1000000000000000000", expiry)
        
        # 5. Create Voucher
        print("\n[5] Creating Voucher...")
        voucher = cm.create_voucher(pay_to, amount)
        voucher["paymentId"] = payment_id
        
        # 6. Settle Voucher
        print("\n[6] Settling Voucher...")
        # Infer settlement endpoint (Resource Service)
        # Assuming resource URL base refers to the service root
        base_url = "http://localhost:8787" 
        settle_url = f"{base_url}/api/pay-voucher"
        
        print(f"POST {settle_url}")
        settle_res = await client.post(settle_url, json=voucher)
        
        if settle_res.status_code != 200:
            print(f"Settlement failed: {settle_res.status_code} {settle_res.text}")
            return
        
        print("Settlement Successful!")
        print(settle_res.json())

        # 7. Retry Resource
        print("\n[7] Retrying Protected Resource...")
        retry_res = await client.get(RESOURCE_URL, headers={"x-payment-id": payment_id})
        
        print(f"Status: {retry_res.status_code}")
        if retry_res.status_code == 200:
            print("SUCCESS! Resource content:")
            print(retry_res.json())
        else:
            print(f"Failed to access resource: {retry_res.text}")

if __name__ == "__main__":
    asyncio.run(main())
