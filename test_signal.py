import requests

url = "http://127.0.0.1:8000/webhook"
payload = {
    "passphrase": "MySecretBotPassword99!",
    "ticker": "SOLUSDT",
    "action": "BUY",
    "price": 142.50,
    "timeframe": "4h",
    "strategy_name": "Institutional_Breakout_V5"
}

print("🚀 Launching validation payload to FastAPI gateway loop...")
try:
    response = requests.post(url, json=payload, timeout=15)
    print(f"📡 Gateway HTTP Response Status: {response.status_code}")
    print(f"📦 Response JSON Content Summary:\n{response.json()}")
except Exception as e:
    print(f"❌ Testing sequence broke down due to communication issue: {e}")