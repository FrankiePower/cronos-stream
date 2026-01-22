
import asyncio
import os
import sys
import json
import time

# Add Host to path to reuse library code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../a2a/a2a-service")))

try:
    from host.channel_manager import ChannelManager
    from eth_account import Account
    import httpx
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

async def test_streaming_reuse():
    print("--- 🌊 Verifying Streaming Channel Reuse ---")
    
    # 1. Config
    load_dotenv("a2a/a2a-service/.env")
    pk = os.getenv("X402_AGENT_PRIVATE_KEY")
    if not pk:
        print("❌ X402_AGENT_PRIVATE_KEY missing")
        return

    # 2. Setup Manager
    # We use a randomized channel ID or load the existing one to be safe?
    # Actually, let's load the one created by the real agent to show interoperability
    STATE_FILE = "a2a/a2a-service/channel_state.json"
    channel_id = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
            channel_id = state.get("channelId")
    
    if not channel_id:
        print("⚠️  No existing channel found. Using random new one.")
        import secrets
        channel_id = "0x" + secrets.token_hex(32)

    owner = Account.from_key(pk)
    cm = ChannelManager(pk, channel_id, owner.address)
    sequencer_url = "http://localhost:4001"
    
    print(f"🔹 Channel ID: {channel_id}")
    print(f"🔹 Owner:      {owner.address}")
    
    # 3. Ensure Channel is Open (On-Chain/Sequencer sync)
    print("\n[Step 1] Syncing with Sequencer...")
    # Use a fixed expiry for consistence in this test run or just let it create new if stale
    await cm.ensure_channel(sequencer_url, "2000000", int(time.time()) + 3600)
    print(f"✅ Synced. Current Sequence Number from Sequencer: {cm.sequence_number}")
    
    # 4. Generate Voucher 1
    print("\n[Step 2] Generating Voucher #1 (Amount: 1 USDC)...")
    v1 = cm.create_voucher(owner.address, 1000000) 
    print(f"   🎫 Voucher Nonce: {v1['sequenceNumber']}")
    print(f"   ✍️  Signature:    {v1['userSignature'][:10]}...")
    
    # 5. Generate Voucher 2
    print("\n[Step 3] Generating Voucher #2 (Amount: 2 USDC)...")
    v2 = cm.create_voucher(owner.address, 2000000)
    print(f"   🎫 Voucher Nonce: {v2['sequenceNumber']}")
    print(f"   ✍️  Signature:    {v2['userSignature'][:10]}...")
    
    # 6. Verify Increment
    try:
        n1 = int(v1['sequenceNumber'])
        n2 = int(v2['sequenceNumber'])
        
        if n2 == n1 + 1:
            print("\n✅ SUCCESS: Sequence Number incremented correctly!")
            print("   This proves the channel is being reused for sequential streaming payments.")
        else:
            print(f"\n❌ FAILURE: Sequence Number did not increment ({n1} -> {n2})")
            
    finally:
        print("\n[Step 5] Cleaning Up (Closing Channel)...")
        if cm:
            cm.close_channel(sequencer_url)

if __name__ == "__main__":
    asyncio.run(test_streaming_reuse())
