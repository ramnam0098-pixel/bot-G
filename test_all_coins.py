import asyncio
import ccxt.async_support as ccxt

# 1. Stablecoins and fiat currencies to ignore
EXCLUDED_BASES = ["USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDE", "EUR", "AEUR"]

async def check_order_book_pressure(exchange, symbol: str, threshold: float = 1.5):
    """Fetches the live order book for a coin and calculates volume imbalance."""
    try:
        orderbook = await exchange.fetch_order_book(symbol, limit=50)
        total_bid_volume = sum([bid[1] for bid in orderbook['bids']])
        total_ask_volume = sum([ask[1] for ask in orderbook['asks']])
        
        if total_bid_volume > (total_ask_volume * threshold):
            return "BUY_PRESSURE", total_bid_volume, total_ask_volume
        elif total_ask_volume > (total_bid_volume * threshold):
            return "SELL_PRESSURE", total_bid_volume, total_ask_volume
        else:
            return "NEUTRAL", total_bid_volume, total_ask_volume
    except Exception as e:
        return f"ERROR ({type(e).__name__})", 0, 0

async def run_batch_test():
    exchange = ccxt.binance({
        'hostname': 'api1.binance.com', 
        'timeout': 15000,
        'enableRateLimit': True
    })
    
    print("Connecting to Binance live data feeds...")
    
    try:
        tickers = await exchange.fetch_tickers()
        
        volatile_pairs = []
        for symbol, ticker in tickers.items():
            if symbol.endswith("/USDT"):
                base_coin = symbol.split("/")[0]
                if base_coin not in EXCLUDED_BASES:
                    quote_volume = ticker.get('quoteVolume', 0)
                    if quote_volume > 0:
                        volatile_pairs.append((symbol, quote_volume))
        
        # 2. Sort by volume and grab the top 50 pairs
        volatile_pairs.sort(key=lambda x: x[1], reverse=True)
        top_pairs = [pair[0] for pair in volatile_pairs[:50]]
        
        print(f"Successfully loaded the top {len(top_pairs)} volume leaders.")
        print("Scanning order books in batches to protect API rate limits...\n")
        
        results = []
        chunk_size = 10  # Process 10 coins concurrently per batch
        
        # 3. Batch processing loop
        for i in range(0, len(top_pairs), chunk_size):
            chunk = top_pairs[i:i+chunk_size]
            print(f"Scanning batch {i//chunk_size + 1}/{len(top_pairs)//chunk_size}...")
            
            tasks = [check_order_book_pressure(exchange, sym) for sym in chunk]
            chunk_results = await asyncio.gather(*tasks)
            results.extend(chunk_results)
            
            # 1-second cooldown between batches to stay under the rate limit ceiling
            await asyncio.sleep(1.0)
        
        # 4. Format and print the consolidated results
        print(f"\n{'SYMBOL':<12} | {'STATUS':<16} | {'BID VOLUME (BUY)':<18} | {'ASK VOLUME (SELL)':<18}")
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
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(run_batch_test())