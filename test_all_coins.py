import asyncio
import ccxt.async_support as ccxt

# 1. Define the stablecoins/fiat we want to IGNORE
EXCLUDED_BASES = ["USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDE", "EUR", "AEUR"]

async def check_order_book_pressure(exchange, symbol: str, threshold: float = 1.5):
    """Fetches the live order book and calculates the imbalance."""
    try:
        # Fetch top 50 levels of the order book
        orderbook = await exchange.fetch_order_book(symbol, limit=50)
        total_bid_volume = sum([bid[1] for bid in orderbook['bids']])
        total_ask_volume = sum([ask[1] for ask in orderbook['asks']])
        
        # Determine dominance based on your 1.5x threshold
        if total_bid_volume > (total_ask_volume * threshold):
            return "BUY_PRESSURE", total_bid_volume, total_ask_volume
        elif total_ask_volume > (total_bid_volume * threshold):
            return "SELL_PRESSURE", total_bid_volume, total_ask_volume
        else:
            return "NEUTRAL", total_bid_volume, total_ask_volume
    except Exception as e:
        return "ERROR", 0, 0

async def run_batch_test():
    exchange = ccxt.binance()
    print("Fetching all live Binance markets...\n")
    
    try:
        # 2. Fetch all 24h tickers to analyze volume
        tickers = await exchange.fetch_tickers()
        
        volatile_pairs = []
        for symbol, ticker in tickers.items():
            # Only look at /USDT pairs
            if symbol.endswith("/USDT"):
                base_coin = symbol.split("/")[0]
                
                # 3. Filter out the stablecoins
                if base_coin not in EXCLUDED_BASES:
                    quote_volume = ticker.get('quoteVolume', 0)
                    if quote_volume > 0:
                        volatile_pairs.append((symbol, quote_volume))
        
        # 4. Sort by 24h volume (highest first) and take the top 15
        volatile_pairs.sort(key=lambda x: x[1], reverse=True)
        top_pairs = [pair[0] for pair in volatile_pairs[:15]]
        
        print(f"Top 15 Volatile Pairs by Volume:\n{', '.join(top_pairs)}\n")
        print("Scanning Live Order Books (Threshold: 1.5x)...\n")
        
        # 5. Run the order book logic on all 15 coins at the exact same time
        tasks = [check_order_book_pressure(exchange, sym) for sym in top_pairs]
        results = await asyncio.gather(*tasks)
        
        # 6. Display the results cleanly
        for sym, (status, bid_vol, ask_vol) in zip(top_pairs, results):
            if status == "BUY_PRESSURE":
                print(f"🟢 [CONFIRMED BUY]  {sym:<10} | Bids: {bid_vol:>10.2f} | Asks: {ask_vol:>10.2f}")
            elif status == "SELL_PRESSURE":
                print(f"🔴 [CONFIRMED SELL] {sym:<10} | Bids: {bid_vol:>10.2f} | Asks: {ask_vol:>10.2f}")
            else:
                print(f"🟡 [REJECTED]       {sym:<10} | Bids: {bid_vol:>10.2f} | Asks: {ask_vol:>10.2f} (Balanced)")

    finally:
        await exchange.close()

if __name__ == "__main__":
    # Run the async event loop
    asyncio.run(run_batch_test())