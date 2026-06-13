import os
import httpx
import ccxt.async_support as ccxt
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(redirect_slashes=True)

# --- Discord Function ---
async def send_discord(message: str):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    async with httpx.AsyncClient() as client:
        try:
            await client.post(webhook_url, json={"content": message})
        except Exception as e:
            print(f"Discord error: {e}")

# --- Binance Order Book Function ---
async def check_order_book_pressure(symbol: str) -> str:
    """
    Fetches the live order book from Binance and compares Buy vs Sell volume.
    """
    # CCXT requires symbols in 'BTC/USDT' format. TradingView sends 'BTCUSDT'.
    # This formats it correctly if there is no slash.
    if "/" not in symbol and "USDT" in symbol:
        symbol = symbol.replace("USDT", "/USDT")

    exchange = ccxt.binance()
    try:
        # Fetch the top 50 bids (buyers) and asks (sellers)
        orderbook = await exchange.fetch_order_book(symbol, limit=50)
        
        # Calculate total volume for the top 50 levels
        total_bid_volume = sum([bid[1] for bid in orderbook['bids']])
        total_ask_volume = sum([ask[1] for ask in orderbook['asks']])
        
        print(f"[{symbol}] Buy Volume: {total_bid_volume:.2f} | Sell Volume: {total_ask_volume:.2f}")
        
        # Determine the pressure (Require 50% more volume to confirm dominance)
        if total_bid_volume > (total_ask_volume * 1.5):
            return "STRONG_BUY_PRESSURE"
        elif total_ask_volume > (total_bid_volume * 1.5):
            return "STRONG_SELL_PRESSURE"
        else:
            return "NEUTRAL_PRESSURE"
            
    except Exception as e:
        print(f"Binance fetch error: {e}")
        return "ERROR"
    finally:
        # Crucial: Close the connection to prevent memory leaks
        await exchange.close()

# --- Webhook Route ---
@app.post("/webhook")
@app.post("/webhook/")
async def handle_webhook(request: Request):
    data = await request.json()
    
    # 1. Validate Passphrase
    expected_pass = os.getenv("WEBHOOK_PASSPHRASE")
    if data.get("passphrase") != expected_pass:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    symbol = data.get("symbol", "BTC/USDT")
    side = data.get("side", "UNKNOWN").upper()
    price = data.get("price", "N/A")
    
    # 2. Fetch Live Binance Data
    print("Signal received. Fetching Binance Order Book...")
    order_book_status = await check_order_book_pressure(symbol)
    
    # 3. Decision Logic
    # Only send the alert if TradingView and the Order Book agree!
    trade_approved = False
    if side == "BUY" and order_book_status == "STRONG_BUY_PRESSURE":
        trade_approved = True
    elif side == "SELL" and order_book_status == "STRONG_SELL_PRESSURE":
        trade_approved = True

    # 4. Format and Send Discord Alert
    if trade_approved:
        msg = f"🟢 **CONFIRMED TRADE** 🟢\n**Action:** {side}\n**Pair:** {symbol}\n**Price:** {price}\n**Book Pressure:** {order_book_status}"
    else:
        msg = f"🟡 **TRADE REJECTED** 🟡\n**Action:** {side}\n**Pair:** {symbol}\n**Reason:** Order book volume ({order_book_status}) does not support the TradingView signal."
        
    await send_discord(msg)
    
    return {"status": "success", "approved": trade_approved}