from fastapi import FastAPI, Request, HTTPException
import ccxt.async_support as ccxt
import httpx

app = FastAPI()

# Configuration
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1513436428984647700/FYDJn0FM2NAnGhffa1pruB5THs8PhrqVFIdcc0_CimyrarUCDqxxtvXzh1YVw6nppLyn"
ORDER_BOOK_THRESHOLD = 1.5
EXCLUDED_BASES = ["USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDE", "EUR", "AEUR"]

async def send_to_discord(content: str):
    """Utility function to pass logs forward to Discord channel streams."""
    async with httpx.AsyncClient() as client:
        payload = {"content": content}
        try:
            await client.post(DISCORD_WEBHOOK_URL, json=payload)
        except Exception as e:
            print(f"Discord notification failed: {e}")

@app.post("/webhook/")
async def handle_tradingview_webhook(request: Request):
    try:
        # 1. Parse incoming data frame from TradingView
        data = await request.json()
        raw_symbol = data.get("symbol")  # Expected format: "BTCUSDT" or "SOLUSDT"
        action = data.get("action")      # Expected format: "BUY" or "SELL"
        
        if not raw_symbol or not action:
            raise HTTPException(status_code=400, detail="Missing critical fields.")
            
        # 2. Reformat trading symbol name structurally for standard CCXT formatting
        # Converts "BTCUSDT" -> "BTC/USDT"
        if "USDT" in raw_symbol and "/" not in raw_symbol:
            symbol = raw_symbol.replace("USDT", "/USDT")
        else:
            symbol = raw_symbol

        # 3. Instantiate isolated endpoint parameters to avoid regional network blocks
        exchange = ccxt.binance({
            'hostname': 'api1.binance.com',
            'timeout': 15000,
            'enableRateLimit': True
        })
        
        try:
            # 4. Pull live order book array depth profiles
            orderbook = await exchange.fetch_order_book(symbol, limit=50)
            total_bid_volume = sum([bid[1] for bid in orderbook['bids']])
            total_ask_volume = sum([ask[1] for ask in orderbook['asks']])
            
            # 5. Evaluate order matrix pressures against technical signal direction
            is_valid = False
            if action == "BUY" and total_bid_volume > (total_ask_volume * ORDER_BOOK_THRESHOLD):
                is_valid = True
            elif action == "SELL" and total_ask_volume > (total_bid_volume * ORDER_BOOK_THRESHOLD):
                is_valid = True
                
            # 6. Push verified decisions out to the interface endpoint
            if is_valid:
                alert_msg = f"🟢 **TRADE CONFIRMED**\nAsset: `{symbol}`\nAction: `{action}`\nBid Vol: `{total_bid_volume:.2f}` | Ask Vol: `{total_ask_volume:.2f}`"
            else:
                alert_msg = f"🟡 **TRADE REJECTED** (Insufficient order book pressure)\nAsset: `{symbol}`\nAction: `{action}`\nBid Vol: `{total_bid_volume:.2f}` | Ask Vol: `{total_ask_volume:.2f}`"
                
            await send_to_discord(alert_msg)
            
        finally:
            await exchange.close()
            
        return {"status": "processed", "validated": is_valid}
        
    except Exception as e:
        await send_to_discord(f"❌ **Webhook Error Processing Data Packet**: `{str(e)}`")
        return {"status": "error", "message": str(e)}