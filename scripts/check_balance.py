import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Resolve paths relative to this script or project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, "a2a", "a2a-service", ".env")
load_dotenv(env_path)

RPC_URL = "https://evm-t3.cronos.org/"
PRIVATE_KEY = os.getenv("X402_AGENT_PRIVATE_KEY")
USDC_ADDRESS = "0xc01efAaF7C5C61bEbFAeb358E1161b537b8bC0e0"

ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}
]

def main():
    if not PRIVATE_KEY:
        print("Error: X402_AGENT_PRIVATE_KEY not found in .env")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = Account.from_key(PRIVATE_KEY)
    address = account.address
    
    print(f"--- Wallet Check ---")
    print(f"Address: {address}")
    
    # Check Native (TCRO)
    balance_wei = w3.eth.get_balance(address)
    balance_tcro = w3.from_wei(balance_wei, 'ether')
    print(f"Native Balance: {balance_tcro} TCRO")
    
    # Check USDC
    usdc = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
    try:
        symbol = usdc.functions.symbol().call()
        decimals = usdc.functions.decimals().call()
        balance_usdc_raw = usdc.functions.balanceOf(address).call()
        balance_usdc = balance_usdc_raw / (10 ** decimals)
        
        print(f"Token Balance:  {balance_usdc} {symbol}")
        print(f"Raw Token Bal:  {balance_usdc_raw}")
    except Exception as e:
        print(f"Error checking USDC: {e}")

if __name__ == "__main__":
    main()
