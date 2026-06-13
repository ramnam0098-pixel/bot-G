import os
import httpx
from datetime import datetime

async def send_discord_signal(signal_data: dict, market_metrics: dict):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url or "your/actual/webhook" in webhook_url:
        print("⚠️ Notification bypassed: Valid Discord Webhook URL not configured.")
        return

    action = signal_data['action'].upper()
    embed_color = 0x2ecc71 if action == "BUY" else 0xe74c3c
    clean_ticker = signal_data['ticker'].upper()
    base_asset = clean_ticker.replace("USDT", "")
    
    payload = {
        "username": "Sovereign Quant Bot",
        "avatar_url": "https://i.imgur.com/w8R78pU.png",
        "embeds": [{
            "title": f"🚨 SYSTEM SIGNAL MATRIX: {action} {clean_ticker}",
            "description": f"Strategy Execution Layer: `{signal_data['strategy_name']}`",
            "color": embed_color,
            "fields": [
                {"name": "📊 Setup Core", "value": f"**Trigger:** `${signal_data['price']:,}`\n**Timeframe:** `{signal_data['timeframe']}`", "inline": True},
                {"name": "💰 Risk Allocation Rule", "value": f"**Allocation:** `{market_metrics.get('position_size_tokens')}` {base_asset}\n**Notional:** `${market_metrics.get('position_size_usd')}`", "inline": True},
                {"name": "🛡️ Volatility Targets (ATR)", "value": f"**Stop Loss:** `${market_metrics.get('stop_loss')}`\n**Take Profit 1:** `${market_metrics.get('tp_1')}`\n**Take Profit 2:** `${market_metrics.get('tp_2')}`", "inline": False},
                {"name": "📈 Trend Moving Averages", "value": f"**EMA (20):** `${market_metrics.get('ema_20')}`\n**EMA (50):** `${market_metrics.get('ema_50')}`\n**SMA (100):** `${market_metrics.get('sma_100')}`", "inline": True},
                {"name": "⏱️ Momentum Oscillators", "value": f"**RSI (14):** `{market_metrics.get('rsi')}`\n**Stoch %K:** `{market_metrics.get('stoch_k')}`\n**Williams %R:** `{market_metrics.get('williams_r')}`", "inline": True},
                {"name": "🌀 Volatility & Waves", "value": f"**MACD Hist:** `{market_metrics.get('macd_hist')}`\n**CCI:** `{market_metrics.get('cci')}`\n**ROC:** `{market_metrics.get('roc')}%`", "inline": True},
                {"name": "🌐 Bollinger Band Boundaries", "value": f"**Upper Band:** `${market_metrics.get('bb_upper')}`\n**Lower Band:** `${market_metrics.get('bb_lower')}`", "inline": True},
                {"name": "🔍 Order Book Liquidity", "value": f"**Imbalance:** `{market_metrics.get('imbalance_ratio', 1.0):.2f}x`\n**OI Contracts:** `{market_metrics.get('open_interest')}`", "inline": True},
                {"name": "🕯️ Active Candlestick Formations", "value": f"`{market_metrics.get('candle_pattern')}`", "inline": False},
                {"name": "🤖 Macro System Judgment", "value": f"**Regime:** `{market_metrics.get('macro_regime')}`\n*Context:* {market_metrics.get('structure_details')}", "inline": False}
            ],
            "footer": {"text": f"Sovereign Quantitative Engine • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(webhook_url, json=payload)
            if res.status_code in [200, 204]:
                print(f"📡 Complete institutional matrix broadcasted to Discord for {clean_ticker}.")
            else:
                print(f"❌ Discord transmission error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"❌ Connection failure dispatching to Discord endpoint: {e}")