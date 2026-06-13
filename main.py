import os
import asyncio
import ccxt.async_support as ccxt_async
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv

from bot.exchange import get_order_book_metrics
from bot.analysis import check_market_structure
from bot.risk import calculate_trade_risk
from bot.notifier import send_discord_signal

load_dotenv()

app = FastAPI(title="Sovereign Async Quant Gateway")

# Configure the CCXT Exchange instance directly targeting the USD-M Futures server (fapi)
exchange_config = {
    'timeout': 10000,
    'enableRateLimit': True,
    # ⚡ PROXY CONFIGURATION (Uncomment and populate if you are running from a geo-blocked IP region):
    # 'aiohttp_proxy': 'http://your_proxy_ip:port', 
}

exchange = ccxt_async.binanceusdm(exchange_config)

class WebhookPayload(BaseModel):
    passphrase: str
    ticker: str
    action: str
    price: float
    timeframe: str
    strategy_name: str

def format_ccxt_symbol(ticker: str) -> str:
    """Converts standard raw exchange strings like SOLUSDT to unified CCXT symbols like SOL/USDT."""
    ticker_clean = ticker.upper().strip()
    if "/" not in ticker_clean:
        if ticker_clean.endswith("USDT"):
            return f"{ticker_clean[:-4]}/USDT"
    return ticker_clean

@app.on_event("startup")
async def startup_event():
    """Pre-caches exchange structures on server startup to prevent concurrent task collisions."""
    try:
        await exchange.load_markets()
        print("🎯 CCXT Futures Market Registry cached successfully. System clear for parallel tasks.")
    except Exception as e:
        print(f"⚠️ Initial market registry load failed: {e}")
        print("💡 Action Required: Verify your hosting environment IP is not geo-blocked by Binance, or supply a valid 'aiohttp_proxy'.")

@app.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook_receiver(payload: WebhookPayload):
    if payload.passphrase != os.getenv("WEBHOOK_PASSPHRASE"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature.")
    
    # Translate ticker format to keep CCXT parsing routines happy
    ccxt_symbol = format_ccxt_symbol(payload.ticker)
    print(f"\n⚡ Processing concurrent pipeline for unified symbol: {ccxt_symbol}")
    
    try:
        # Await both high-speed network endpoints in a single event loop iteration
        exchange_data = await get_order_book_metrics(exchange, ccxt_symbol)
        analysis_data = await check_market_structure(exchange, ccxt_symbol, payload.timeframe)
        
        # Pull raw historical data out for the local risk engine processing layer
        df_candles = analysis_data.pop("raw_df", None)
        risk_data = calculate_trade_risk(ccxt_symbol, payload.action, payload.price, df_candles)
        
        # Merge metrics and ship the compiled dossier matrix over to the live Discord card channel
        market_metrics = {**exchange_data, **analysis_data, **risk_data}
        await send_discord_signal(payload.model_dump(), market_metrics)
        
        return {
            "status": "broadcasted",
            "ticker": ccxt_symbol,
            "execution_targets": {
                "sl": risk_data.get("stop_loss"), 
                "tp1": risk_data.get("tp_1")
            }
        }
        
    except Exception as e:
        print(f"❌ Critical error inside runtime pipeline execution loop: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully tears down open connection pools upon server exit."""
    await exchange.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main.py", host="127.0.0.1", port=8000, reload=True)