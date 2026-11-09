import yfinance as yf
import pandas as pd
import numpy as np
import ta
import os

JOURNAL_FILE = "trading_journal.csv"

def compile_market_signals(df_d, df_h):
    """Processes historical structures and generates complete signal series for plotting."""
    df_h = df_h.copy()
    
    # Calculate Core Indicators across the whole series
    df_h['RSI'] = ta.momentum.RSIIndicator(close=df_h['Close'], window=14).rsi().fillna(50.0)
    df_h['EMA_200'] = ta.trend.EMAIndicator(close=df_h['Close'], window=200).ema_indicator().fillna(df_h['Close'])
    
    macd_obj = ta.trend.MACD(close=df_h['Close'], window=12, window=26, window=9)
    df_h['MACD_Hist'] = macd_obj.macd_diff().fillna(0.0)
    
    atr_obj = ta.volatility.AverageTrueRange(high=df_h['High'], low=df_h['Low'], close=df_h['Close'], window=14)
    df_h['ATR'] = atr_obj.average_true_range().fillna(df_h['Close'] * 0.002)
    
    # Compute Rolling Extremes for boundaries
    df_h['Recent_Low'] = df_h['Low'].rolling(window=24).min()
    df_h['Recent_High'] = df_h['High'].rolling(window=24).max()
    
    # Establish signals across the dataframe timeline
    df_h['Signal'] = "HOLD"
    
    for i in range(len(df_h)):
        if i < 200: continue
        price = df_h['Close'].iloc[i]
        rsi = df_h['RSI'].iloc[i]
        ema = df_h['EMA_200'].iloc[i]
        hist = df_h['MACD_Hist'].iloc[i]
        r_low = df_h['Recent_Low'].iloc[i-1] if i > 0 else price
        r_high = df_h['Recent_High'].iloc[i-1] if i > 0 else price
        
        if (rsi < 35 or (price <= (r_low * 1.005))) and (price > ema) and (hist > 0):
            df_h['Signal'].iloc[i] = "BUY"
        elif (rsi > 65 or (price >= (r_high * 0.995))) and (price < ema) and (hist < 0):
            df_h['Signal'].iloc[i] = "SELL"
            
    return df_h

# --- ENGINE JOURNAL DATABANK CORE ---
def load_journal():
    if os.path.exists(JOURNAL_FILE):
        return pd.read_csv(JOURNAL_FILE)
    return pd.DataFrame(columns=["Timestamp", "Asset", "Type", "Direction", "Entry_Price", "SL", "TP", "Status", "Profit_Loss_ZAR"])

def log_trade(asset, trade_type, direction, entry, sl, tp, status="OPEN", pl=0.0):
    df = load_journal()
    new_row = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Asset": asset, "Type": trade_type, "Direction": direction,
        "Entry_Price": entry, "SL": sl, "TP": tp, "Status": status, "Profit_Loss_ZAR": pl
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False)
