import pandas as pd
import numpy as np

async def check_market_structure(exchange, ticker: str, macro_timeframe: str = "4h"):
    try:
        candles = await exchange.fetch_ohlcv(ticker, timeframe=macro_timeframe, limit=150)
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        close_series, high_series, low_series = df['close'], df['high'], df['low']
        
        # --- Indicators Matrix ---
        df['ema_20'] = close_series.ewm(span=20, adjust=False).mean()
        df['ema_50'] = close_series.ewm(span=50, adjust=False).mean()
        df['sma_100'] = close_series.rolling(window=100).mean()
        
        delta = close_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['rsi'] = 100 - (100 / (1 + (gain / loss)))
        
        df['macd_line'] = close_series.ewm(span=12, adjust=False).mean() - close_series.ewm(span=26, adjust=False).mean()
        df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd_line'] - df['macd_signal']
        
        df['bb_mid'] = close_series.rolling(window=20).mean()
        df['bb_std'] = close_series.rolling(window=20).std()
        df['bb_upper'] = df['bb_mid'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * 2)
        
        low_14, high_14 = low_series.rolling(window=14).min(), high_series.rolling(window=14).max()
        df['stoch_k'] = ((close_series - low_14) / (high_14 - low_14)) * 100
        df['williams_r'] = ((high_14 - close_series) / (high_14 - low_14)) * -100
        
        tp = (high_series + low_series + close_series) / 3
        df['cci'] = (tp - tp.rolling(window=20).mean()) / (0.015 * tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True))
        df['roc'] = ((close_series - close_series.shift(12)) / close_series.shift(12)) * 100

        last_idx = df.index[-1]
        indicators = {
            "rsi": round(df.at[last_idx, 'rsi'], 2) if not pd.isna(df.at[last_idx, 'rsi']) else 50.0,
            "ema_20": round(df.at[last_idx, 'ema_20'], 2), "ema_50": round(df.at[last_idx, 'ema_50'], 2),
            "sma_100": round(df.at[last_idx, 'sma_100'], 2) if not pd.isna(df.at[last_idx, 'sma_100']) else round(df.at[last_idx, 'ema_50'], 2),
            "macd_hist": round(df.at[last_idx, 'macd_hist'], 4),
            "bb_upper": round(df.at[last_idx, 'bb_upper'], 2), "bb_lower": round(df.at[last_idx, 'bb_lower'], 2),
            "stoch_k": round(df.at[last_idx, 'stoch_k'], 2), "williams_r": round(df.at[last_idx, 'williams_r'], 2),
            "cci": round(df.at[last_idx, 'cci'], 2), "roc": round(df.at[last_idx, 'roc'], 2)
        }

        # --- Candlestick Patterns ---
        c_open, c_close, c_high, c_low = df['open'].iloc[-1], df['close'].iloc[-1], df['high'].iloc[-1], df['low'].iloc[-1]
        p_open, p_close = df['open'].iloc[-2], df['close'].iloc[-2]
        
        patterns = []
        c_body, c_range = abs(c_close - c_open), (c_high - c_low if (c_high - c_low) > 0 else 0.001)
        
        if c_body <= (c_range * 0.1): patterns.append("⚪ Doji")
        if c_body >= (c_range * 0.9): patterns.append("⚡ Marubozu")
        if (min(c_open, c_close) - c_low) > (2 * c_body): patterns.append("🔨 Hammer")
        if (c_high - max(c_open, c_close)) > (2 * c_body): patterns.append("☄️ Shooting Star")
        if p_close < p_open and c_close > c_open and c_close >= p_open: patterns.append("🔥 Bullish Engulfing")
        if p_close > p_open and c_close < c_open and c_close <= p_open: patterns.append("🩸 Bearish Engulfing")

        return {
            "macro_regime": "STRONG BULLISH" if c_close > indicators['ema_20'] else "STRONG BEARISH",
            "structure_details": "Asset processed cleanly through complete matrix calculations.",
            "candle_pattern": ", ".join(patterns) if patterns else "No Clear Formations Spoted",
            "raw_df": df,
            **indicators
        }
    except Exception as e:
        print(f"⚠️ Analytics calculation exception: {e}")
        return {
            "macro_regime": "NEUTRAL", "structure_details": f"Error Loop Active: {str(e)}", "candle_pattern": "Scan Failed", "raw_df": None,
            "rsi": "N/A", "ema_20": "N/A", "ema_50": "N/A", "sma_100": "N/A", "macd_hist": "N/A",
            "bb_upper": "N/A", "bb_lower": "N/A", "stoch_k": "N/A", "williams_r": "N/A", "cci": "N/A", "roc": "N/A"
        }