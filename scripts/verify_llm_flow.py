
import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Ensure we can import from the a2a-service module
sys.path.append(os.path.join(os.getcwd(), 'a2a', 'a2a-service'))

try:
    from host.lib.openai.client import OpenAIClient
    from host.lib.openai.planner import PaywallPlanner
    from host.service import PaywallService
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

async def test_planning_flow():
    print("--- 🧠 Verifying LLM Planning with REAL Agents ---")
    
    # 1. Load Env
    load_dotenv("a2a/a2a-service/.env")
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY missing.")
        return

    # 2. Setup Service & Planner
    service = PaywallService()
    client = OpenAIClient(model="gpt-3.5-turbo")
    planner = PaywallPlanner(client)
    print("✅ Service & Planner Initialized")

    # 3. Discover Real Agents
    discovery_url = "http://localhost:8787"
    print(f"📡 Discovering agents from {discovery_url}...")
    
    real_agents = await service.discover_agents([discovery_url])
    
    if not real_agents:
        print(f"❌ No agents found at {discovery_url}. Is the Resource Service running?")
        return
        
    print(f"✅ Found {len(real_agents)} Agent(s):")
    for a in real_agents:
        print(f"   - Name: {a['name']}")
        print(f"     URL: {a['baseUrl']}")
        resources = a.get('card', {}).get('resources', [])
        print(f"     Resources: {len(resources)} items")

    # 4. Test Query: "Get premium content"
    # The demo agent usually exposes a resource descriptions like "Premium Content" or "Cat Picture"
    query = "I want to access the premium content."
    print(f"\n🔎 Query: '{query}'")
    
    choice = await planner.choose_target(query, real_agents)
    
    if choice:
        agent_idx = choice['agentIndex']
        chosen_agent = real_agents[agent_idx]
        print(f"✅ SUCCESS: LLM selected Agent '{chosen_agent['name']}'")
        print(f"   Reason: {choice.get('reason')}")
    else:
        print(f"❌ FAILURE: LLM could not decide.")

if __name__ == "__main__":
    asyncio.run(test_planning_flow())
