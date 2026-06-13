import httpx
import asyncio

URL = "https://bot-g-s6ej.onrender.com/webhook"
PASSPHRASE = "MySecretBotPassword99!" # Must match Render Environment Variable

async def send_test():
    payload = {
        "passphrase": PASSPHRASE,
        "symbol": "BTC/USDT",
        "side": "BUY",
        "price": 65000.00
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(URL, json=payload)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_test())