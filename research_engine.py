import yfinance as yf
import pandas as pd
import numpy as np
import ta

def compile_market_signals(df_d, df_h):
    """Processes advanced intermarket data arrays to output precise direction targets."""
    # Ensure flat data series parsing
    close_h = pd.Series(df_h['Close'].values.flatten())
    high_h = pd.Series(df_h['High'].values.flatten())
    low_h = pd.Series(df_h['Low'].values.flatten())
    
    # 📈 Advanced Indicator Layer
    rsi_h = ta.momentum.RSIIndicator(close=close_h, window=14).rsi().fillna(50.0).values[-1]
    ema_h = ta.trend.EMAIndicator(close=close_h, window=200).ema_indicator().fillna(close_h.iloc[-1]).values[-1]
    
    # Advanced research layer: Adding MACD to confirm momentum direction
    macd_obj = ta.trend.MACD(close=close_h, window_fast=12, window_slow=26, window_sign=9)
    macd_line = macd_obj.macd().fillna(0.0).values[-1]
    macd_signal = macd_obj.macd_signal().fillna(0.0).values[-1]
    macd_histogram = macd_line - macd_signal
    
    # Dynamic Volatility calculation (Average True Range)
    atr_series = ta.volatility.AverageTrueRange(high=high_h, low=low_h, close=close_h, window=14).average_true_range()
    hourly_atr = atr_series.fillna(close_h.iloc[-1] * 0.002).values[-1]
    
    price = float(close_h.iloc[-1])
    recent_low = float(df_h['Low'].tail(24).min().iloc[0] if isinstance(df_h['Low'].tail(24).min(), pd.Series) else df_h['Low'].tail(24).min())
    recent_high = float(df_h['High'].tail(24).max().iloc[0] if isinstance(df_h['High'].tail(24).max(), pd.Series) else df_h['High'].tail(24).max())
    
    # Trend alignment logic
    is_uptrend = price > ema_h
    is_downtrend = price < ema_h
    macd_bullish = macd_histogram > 0
    macd_bearish = macd_histogram < 0

    # Strict multi-layer confirmation formula
    if (rsi_h < 35 or (price <= (recent_low * 1.005))) and is_uptrend and macd_bullish:
        signal, direction = "🚀 EXECUTE BUY (GO LONG)", "LONG"
    elif (rsi_h > 65 or (price >= (recent_high * 0.995))) and is_downtrend and macd_bearish:
        signal, direction = "💥 EXECUTE SELL SHORT (GO SHORT)", "SHORT"
    else:
        signal, direction = "⏳ HOLD POSITION / PRESERVE CASH", "HOLD"
        
    return {
        "price": price, "hourly_rsi": rsi_h, "hourly_ema": ema_h, 
        "hourly_atr": hourly_atr, "signal": signal, "direction": direction,
        "is_uptrend": is_uptrend, "macd_hist": macd_histogram
    }
