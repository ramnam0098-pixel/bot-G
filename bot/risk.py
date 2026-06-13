import os
import pandas as pd  # 👈 Added missing import

def calculate_trade_risk(ticker: str, action: str, entry_price: float, df: any):
    account_balance = float(os.getenv("TOTAL_ACCOUNT_BALANCE", 10000.0))
    risk_percent = float(os.getenv("MAX_RISK_PER_TRADE_PCT", 1.0)) / 100.0
    dollar_amount_at_risk = account_balance * risk_percent

    try:
        if df is None or df.empty:
            raise ValueError("No historical dataframe passed to risk engine.")
            
        # Calculate ATR directly from the provided data
        df['prev_close'] = df['close'].shift(1)
        tr = pd.concat([df['high'] - df['low'], (df['high'] - df['prev_close']).abs(), (df['low'] - df['prev_close']).abs()], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        atr_value = df['atr'].iloc[-1]
        
        if pd.isna(atr_value) or atr_value == 0:
            atr_value = entry_price * 0.015 
            
        risk_buffer = atr_value * 1.5
        stop_loss = entry_price - risk_buffer if action.upper() == "BUY" else entry_price + risk_buffer
        tp_1 = entry_price + (risk_buffer * 1.5) if action.upper() == "BUY" else entry_price - (risk_buffer * 1.5)
        tp_2 = entry_price + (risk_buffer * 3.0) if action.upper() == "BUY" else entry_price - (risk_buffer * 3.0)
        
        risk_per_unit = abs(entry_price - stop_loss)
        position_size_tokens = dollar_amount_at_risk / risk_per_unit
        
        return {
            "atr": round(atr_value, 4), "stop_loss": round(stop_loss, 4),
            "tp_1": round(tp_1, 4), "tp_2": round(tp_2, 4),
            "max_loss_usd": round(dollar_amount_at_risk, 2),
            "position_size_tokens": round(position_size_tokens, 3),
            "position_size_usd": round(position_size_tokens * entry_price, 2)
        }
    except Exception as e:
        print(f"⚠️ Risk module safety override triggered: {e}")
        # Fallback parameters if data is unavailable
        fallback_gap = entry_price * 0.02
        stop_loss = entry_price - fallback_gap if action.upper() == "BUY" else entry_price + fallback_gap
        return {
            "atr": 0.0, "stop_loss": round(stop_loss, 4), "tp_1": round(entry_price * 1.03, 4), "tp_2": round(entry_price * 1.06, 4),
            "max_loss_usd": round(dollar_amount_at_risk, 2), "position_size_tokens": 1.0, "position_size_usd": entry_price
        }