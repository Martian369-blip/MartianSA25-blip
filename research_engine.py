import yfinance as yf
import pandas as pd
import numpy as np
import ta
import os
from datetime import datetime

JOURNAL_FILE = "trading_journal.csv"

def compile_market_signals(df_d, df_h):
    """Processes historical arrays and tracks multi-timeframe structural signals."""
    df_h = df_h.copy()
    
    # Isolate Close array to bypass Pandas multidimensional serialization bugs
    close_array = df_h['Close'].values.flatten()
    high_array = df_h['High'].values.flatten()
    low_array = df_h['Low'].values.flatten()
    
    close_series = pd.Series(close_array)
    
    # Calculate indicators using clean single-dimension series formatting
    df_h['RSI'] = ta.momentum.RSIIndicator(close=close_series, window=14).rsi().fillna(50.0).values
    df_h['EMA_200'] = ta.trend.EMAIndicator(close=close_series, window=200).ema_indicator().fillna(close_series).values
    
    macd_obj = ta.trend.MACD(close=close_series, window=12, window=26, window=9)
    df_h['MACD_Hist'] = macd_obj.macd_diff().fillna(0.0).values
    
    atr_obj = ta.volatility.AverageTrueRange(
        high=pd.Series(high_array), low=pd.Series(low_array), close=close_series, window=14
    )
    df_h['ATR'] = atr_obj.average_true_range().fillna(close_series * 0.002).values
    
    df_h['Recent_Low'] = df_h['Low'].rolling(window=24).min()
    df_h['Recent_High'] = df_h['High'].rolling(window=24).max()
    
    df_h['Signal'] = "HOLD"
    
    # Deep algorithmic indexing execution loop
    for i in range(len(df_h)):
        if i < 200: 
            continue
        price = float(close_array[i])
        rsi = float(df_h['RSI'].iloc[i])
        ema = float(df_h['EMA_200'].iloc[i])
        hist = float(df_h['MACD_Hist'].iloc[i])
        r_low = float(df_h['Recent_Low'].iloc[i-1]) if i > 0 else price
        r_high = float(df_h['Recent_High'].iloc[i-1]) if i > 0 else price
        
        if (rsi < 35 or (price <= (r_low * 1.005))) and (price > ema) and (hist > 0):
            df_h.loc[df_h.index[i], 'Signal'] = "BUY"
        elif (rsi > 65 or (price >= (r_high * 0.995))) and (price < ema) and (hist < 0):
            df_h.loc[df_h.index[i], 'Signal'] = "SELL"
            
    return df_h

def load_journal():
    """Reads or initiates the local tracking databank framework."""
    if os.path.exists(JOURNAL_FILE):
        try:
            return pd.read_csv(JOURNAL_FILE)
        except Exception:
            pass
    return pd.DataFrame(columns=["Timestamp", "Asset", "Type", "Direction", "Entry_Price", "SL", "TP", "Status", "Profit_Loss_ZAR"])

def log_trade(asset, trade_type, direction, entry, sl, tp, status="OPEN", pl=0.0):
    """Commits individual execution transactions directly to the ledger sheet."""
    df = load_journal()
    new_row = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Asset": asset, "Type": trade_type, "Direction": direction,
        "Entry_Price": float(entry), "SL": float(sl), "TP": float(tp), 
        "Status": status, "Profit_Loss_ZAR": float(pl)
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False)
