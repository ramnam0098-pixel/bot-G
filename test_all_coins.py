import asyncio
import ccxt.async_support as ccxt

# 1. Define stablecoins and fiat currencies to ignore
EXCLUDED_BASES = ["USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDE", "EUR", "AEUR"]

async def check_order_book_pressure(exchange, symbol: str, threshold: float = 1.5):
    """
    Fetches the live order book for a single coin and calculates volume imbalance.
    """
    try:
        # Fetch top 50 bids (buyers) and asks (sellers)
        orderbook = await exchange.fetch_order_book(symbol, limit=50)
        total_bid_volume = sum([bid[1] for bid in orderbook['bids']])
        total_ask_volume = sum([ask[1] for ask in orderbook['asks']])
        
        # Calculate market pressure based on the threshold
        if total_bid_volume > (total_ask_volume * threshold):
            return "BUY_PRESSURE", total_bid_volume, total_ask_volume
        elif total_ask_volume > (total_bid_volume * threshold):
            return "SELL_PRESSURE", total_bid_volume, total_ask_volume
        else:
            return "NEUTRAL", total_bid_volume, total_ask_volume
    except Exception as e:
        return f"ERROR ({type(e).__name__})", 0, 0

async def run_batch_test():
    # 2. Initialize Binance with an alternate endpoint to bypass DNS/ISP blockages
    exchange = ccxt.binance({
        'hostname': 'api1.binance.com',  # Alternate official endpoint
        'timeout': 15000,
        'enableRateLimit': True
    })
    
    print("Connecting to Binance live data feeds...\n")
    
    try:
        # 3. Fetch all active 24-hour market tickers
        tickers = await exchange.fetch_tickers()
        
        volatile_pairs = []
        for symbol, ticker in tickers.items():
            # Target only the standard USDT trading pairs
            if symbol.endswith("/USDT"):
                base_coin = symbol.split("/")[0]
                
                # Filter out the non-moving stablecoins
                if base_coin not in EXCLUDED_BASES:
                    quote_volume = ticker.get('quoteVolume', 0)
                    if quote_volume > 0:
                        volatile_pairs.append((symbol, quote_volume))
        
        # 4. Sort all eligible assets by 24h trading volume and isolate the top 15
        volatile_pairs.sort(key=lambda x: x[1], reverse=True)
        top_pairs = [pair[0] for pair in volatile_pairs[:15]]
        
        print(f"Top 15 Most Volatile Pairs Selected:\n{', '.join(top_pairs)}\n")
        print("Scanning Live Order Book Depth (Threshold: 1.5x)...\n")
        
        # 5. Execute asynchronous order book requests for all 15 coins concurrently
        tasks = [check_order_book_pressure(exchange, sym) for sym in top_pairs]
        results = await asyncio.gather(*tasks)
        
        # 6. Clean print out formatting for analysis
        print(f"{'SYMBOL':<12} | {'STATUS':<16} | {'BID VOLUME (BUY)':<18} | {'ASK VOLUME (SELL)':<18}")
        print("-" * 75)
        
        for sym, (status, bid_vol, ask_vol) in zip(top_pairs, results):
            if status == "BUY_PRESSURE":
                print(f"🟢 {sym:<10} | {status:<16} | {bid_vol:>18.2f} | {ask_vol:>18.2f}")
            elif status == "SELL_PRESSURE":
                print(f"🔴 {sym:<10} | {status:<16} | {bid_vol:>18.2f} | {ask_vol:>18.2f}")
            elif "ERROR" in status:
                print(f"❌ {sym:<10} | {status:<16} | {'N/A':>18} | {'N/A':>18}")
            else:
                print(f"🟡 {sym:<10} | {status:<16} | {bid_vol:>18.2f} | {ask_vol:>18.2f}")

    except Exception as e:
        print(f"Critical connection failure: {e}")
        print("Tip: If the error persists, verify your local internet connection status.")
        
    finally:
        # Crucial for preventing unclosed connection resource warnings
        await exchange.close()

if __name__ == "__main__":
    # Initialize the asynchronous execution framework
    asyncio.run(run_batch_test())