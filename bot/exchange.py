import asyncio

async def get_order_book_metrics(exchange, ticker: str):
    try:
        # Fetch order book and open interest concurrently using the unified symbol
        order_book_task = exchange.fetch_order_book(ticker, limit=20)
        oi_task = exchange.fetch_open_interest(ticker)
        
        order_book, oi_data = await asyncio.gather(order_book_task, oi_task)
        
        bids_volume = sum([bid[1] for bid in order_book['bids']])
        asks_volume = sum([ask[1] for ask in order_book['asks']])
        imbalance = bids_volume / asks_volume if asks_volume > 0 else 1.0
        
        open_interest = oi_data[-1]['openInterest'] if isinstance(oi_data, list) else oi_data.get('openInterest', 'N/A')
        if isinstance(open_interest, (int, float)):
            open_interest = f"{open_interest:,.0f}"
            
        return {"imbalance_ratio": imbalance, "open_interest": open_interest}
    except Exception as e:
        print(f"⚠️ Liquidity fetching exception: {e}")
        return {"imbalance_ratio": 1.0, "open_interest": "Exchange Fetch Timeout"}