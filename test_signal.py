import httpx
import asyncio

# Replace with your actual Render URL and Webhook Passphrase
URL = "https://bot-g-s6ej.onrender.com/webhook"
PASSPHRASE = "MySecretBotPassword99!"

async def test_webhook():
    payload = {
        "passphrase": PASSPHRASE,
        "symbol": "BTC/USDT",
        "side": "buy",
        "price": 65000.00
    }

    print(f"Sending signal to: {URL}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(URL, json=payload, timeout=10.0)
            
            if response.status_code == 200:
                print("Success! Signal received by server.")
                print("Response:", response.json())
            else:
                print(f"Failed. Status Code: {response.status_code}")
                print("Response:", response.text)
                
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook())