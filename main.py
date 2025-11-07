import requests
import threading
from concurrent.futures import ThreadPoolExecutor


PROXY = "http://user:pass@ip:port"
RIPPLE_API_URL = "https://s2.ripple.com:443/"
INPUT_FILE = "xrp.txt"
OUTPUT_FILE = "xrp_balances.txt"

def get_xrp_balance(address, proxy=None):
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "method": "account_info",
        "params": [
            {
                "account": address,
                "strict": True,
                "ledger_index": "current",
                "queue": True
            }
        ]
    }

    proxies = {
        "http": proxy,
        "https": proxy
    } if proxy else None

    try:
        response = requests.post(RIPPLE_API_URL, json=data, headers=headers, proxies=proxies, timeout=10)
        response_data = response.json()

        if "result" in response_data and "account_data" in response_data["result"]:
            balance = response_data["result"]["account_data"]["Balance"]
            return int(balance) / 1_000_000  
        else:
            error_message = response_data.get("error_message", response_data.get("Zero", "0"))
            return f"Zero: {error_message}"

    except Exception as e:
        return f"An error occurred: {e}"

def process_address(address, proxy, results_dict, lock):
    balance = get_xrp_balance(address, proxy=proxy)
    with lock:
        results_dict[address] = balance
        print(f"Address: {address}, Balance: {balance} XRP")

def check_balances_from_file(file_path, proxy=None, max_threads=10):
    try:
        with open(file_path, 'r') as file:
            addresses = [line.strip() for line in file if line.strip()]

        results = {}
        lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            for address in addresses:
                executor.submit(process_address, address, proxy, results, lock)

        return results
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return {}

def save_balances_to_file(balances, output_path):
    try:
        with open(output_path, 'w') as file:
            saved_count = 0
            for address, balance in balances.items():
                if isinstance(balance, (int, float)) and balance > 0:
                    file.write(f"{address} => {balance} XRP\n")
                    saved_count += 1
            print(f"\n✅ Results saved to: {output_path}")
            print(f"📊 Saved {saved_count} addresses with balance out of {len(balances)} total addresses")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")

balances = check_balances_from_file(INPUT_FILE)
save_balances_to_file(balances, OUTPUT_FILE)
