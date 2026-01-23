#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import uuid
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory


# 1. Setup
console = Console()
AGENT_URL = "http://localhost:9001/rpc"
DISCOVERY_URL = "http://localhost:8787"
EXPLORER_BASE = "https://explorer.cronos.org/testnet/tx"
SEQUENCER_URL = "http://localhost:4001"
RPC_URL = "https://evm-t3.cronos.org/"

# Global State
PAYMENT_COUNT = 0
PAYMENT_THRESHOLD = 3
LAST_CHANNEL_ID = None

# Ensure imports work if checked out
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from scripts.check_balance import main as check_balance_internal
    from web3 import Web3
    # Redirect stdout to capture balance
    import io
    from contextlib import redirect_stdout
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
except ImportError:
    check_balance_internal = None
    w3 = None

def get_balance():
    if not check_balance_internal:
        return "N/A"
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            check_balance_internal()
        except:
            pass
    out = f.getvalue()
    # Parse "Token Balance: 1000.0 USDC"
    for line in out.splitlines():
        if "Token Balance" in line:
            return line.split(":")[1].strip()
    return "Unknown"

def trigger_settlement(channel_id):
    if not w3:
        console.print("[bold red]❌ Web3 not available. Cannot settle.[/]")
        return
        
    with console.status(f"[bold yellow]💰 Settling Channel {channel_id} (paying merchant)...[/]", spinner="shark"):
        try:
            # Call Sequencer
            res = requests.post(f"{SEQUENCER_URL}/channel/finalize", json={"channelId": channel_id}, timeout=10)
            if res.status_code != 200:
                console.print(f"[bold red]❌ Settlement Failed:[/]\n{res.text}")
                return
            
            data = res.json()
            tx_hash = data.get("transactionHash")
            
            console.print(f"[green]✅ Settlement Initiated. Waiting for confirmation...[/]")
            console.print(f"[dim]Tx: {tx_hash}[/]")
            
            # Wait for receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            status = "[bold green]✅ CONFIRMED[/]" if receipt.status == 1 else "[bold red]❌ REVERTED[/]"
            
            # Show Result
            grid = Table.grid(expand=True)
            grid.add_column(style="bold white")
            grid.add_column(style="cyan")
            grid.add_row("Action", "Channel Settlement")
            grid.add_row("Status", status)
            grid.add_row("Block", str(receipt.blockNumber))
            grid.add_row("Explorer", f"[link={EXPLORER_BASE}/{tx_hash}]View Transaction[/link]")
            
            console.print(Panel(grid, title="Settlement Complete", border_style="gold1"))
            
        except Exception as e:
             console.print(f"[bold red]❌ Error during settlement: {e}[/]")

def send_query(query: str):
    global PAYMENT_COUNT, LAST_CHANNEL_ID
    
    msg_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": msg_id,
                "role": "user",
                "parts": [{
                    "kind": "data",
                    "data": {
                        "discoveryUrls": [DISCOVERY_URL],
                        "query": query
                    }
                }]
            }
        },
        "id": 1
    }
    
    with console.status(f"[bold green]🤖 Agent working on: '{query}'...", spinner="dots"):
        try:
            res = requests.post(AGENT_URL, json=payload, timeout=30)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            console.print(f"[bold red]❌ Request failed: {e}[/]")
            return

    result = data.get("result", {})
    history = result.get("history", [])
    artifacts = result.get("artifacts", [])

    # Display History Flow
    console.print("\n[bold cyan]⚡ Execution Trace:[/]")
    for step in history:
        role = step.get("role", "unknown").upper()
        if role == "AGENT": 
            icon = "🤖" 
            style = "blue"
        else: 
            icon = "👤"
            style = "green"
            
        parts = step.get("parts", [])
        for p in parts:
            text = p.get("text", "")
            if text and not text.startswith("{"):
                console.print(f"[{style}]{icon} {text}[/]")

    # Display Artifacts (The "Rich" Part)
    if artifacts:
        console.print("\n[bold yellow]📜 Settlement & Result:[/]")
        for art in artifacts:
            for p in art.get("parts", []):
                content = p.get("text", "")
                
                # Check for our debug headers
                if "Status: PAID" in content:
                    lines = content.splitlines()
                    
                    # Extract key info
                    info = {}
                    for l in lines:
                        if ":" in l:
                            k, v = l.split(":", 1)
                            info[k.strip()] = v.strip()
                    
                    # Update State
                    LAST_CHANNEL_ID = info.get("Channel")
                    PAYMENT_COUNT += 1
                    
                    # Build Panel
                    grid = Table.grid(expand=True)
                    grid.add_column(style="bold white")
                    grid.add_column(style="cyan")
                    
                    grid.add_row("Payment Status", "[green]PAID[/]")
                    grid.add_row("Protocol", info.get("Method", "Unknown"))
                    grid.add_row("Channel ID", info.get("Channel", "Unknown"))
                    grid.add_row("Voucher Amount", f"{info.get('Voucher Amount', '?')} units")
                    
                    if "Recipient" in info:
                        addr = info["Recipient"]
                        url = f"https://explorer.cronos.org/testnet/address/{addr}"
                        grid.add_row("Recipient", f"[link={url}]{addr}[/link]")
                        
                    console.print(Panel(grid, title=f"Verifiable Settlement ({PAYMENT_COUNT}/{PAYMENT_THRESHOLD})", border_style="green"))
                    
                    # Show the Data Response separately
                    if "[Server Response]" in content:
                        _, json_data = content.split("[Server Response]")
                        try:
                             # Try pretty print json
                             import ast
                             py_obj = ast.literal_eval(json_data.strip())
                             console.print(Panel(json.dumps(py_obj, indent=2), title="Premium Content", border_style="gold1"))
                        except:
                             console.print(Panel(json_data.strip(), title="Premium Content"))
                             
                    # AUTO SETTLEMENT CHECK
                    if PAYMENT_COUNT >= PAYMENT_THRESHOLD:
                        console.print(f"\n[bold magenta]🔄 Auto-Settlement Threshold Reached ({PAYMENT_THRESHOLD} payments)[/]")
                        if LAST_CHANNEL_ID:
                             trigger_settlement(LAST_CHANNEL_ID)
                             PAYMENT_COUNT = 0
                        else:
                             console.print("[red]Cannot settle: No Channel ID found.[/]")

                else:
                    # Fallback for plain logs
                    console.print(Panel(content, title=art.get("name", "Artifact")))

# REPL Loop
def repl():
    session = PromptSession(history=FileHistory('.cli_history'))
    console.print("[bold magenta]Welcome to CronosStream Interactive CLI[/]")
    console.print("Type 'exit' to quit, 'balance' to check funds, 'settle' to force close, or any query.\n")
    
    while True:
        try:
            text = session.prompt("user@cronos-stream > ")
            text = text.strip()
            if not text:
                continue
            
            if text.lower() in ["exit", "quit"]:
                console.print("Bye! 👋")
                break
                
            if text.lower() == "balance":
                bal = get_balance()
                console.print(f"💰 Current Balance: [bold green]{bal}[/]")
                continue
                
            if text.lower() == "settle":
                 if LAST_CHANNEL_ID:
                     trigger_settlement(LAST_CHANNEL_ID)
                     global PAYMENT_COUNT
                     PAYMENT_COUNT = 0
                 else:
                     console.print("[yellow]No active channel known in this session. Using broad scan...[/]")
                     # Fallback to scanning if we haven't paid yet in this session? 
                     # For now let's just warn.
                     console.print("[red]Please make a payment first so I know which channel to settle.[/red]")
                 continue
                 
            if text.lower() == "help":
                 console.print("Commands: balance, settle, exit, help, [any query]")
                 continue
                 
            # Default: Trigger Agent
            if "premium" in text.lower():
                 console.print("[bold magenta]🚀 Starting Multi-Request Simulation...[/]")
                 send_query(text)
                 for i in range(2):
                      time.sleep(1)
                      console.print(f"\n[bold yellow]🔄 Request {i+2}/3: Fetching resource again...[/]")
                      send_query(text)
            else:
                 send_query(text)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

if __name__ == "__main__":
    repl()
