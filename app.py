import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import os
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION INITIALIZATION ---
st.set_page_config(page_title="MARS_BOT V11.0 Desk", page_icon="🛸", layout="wide")

JOURNAL_FILE = "trading_journal.csv"

# ==================== ADVANCED VISUAL THEME ENGINE ====================
st.markdown("""
    <style>
    .metric-card {
        background-color: #121620;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #232936;
        margin-bottom: 10px;
    }
    .hypothesis-box {
        background-color: #1a1c24;
        padding: 15px;
        border-left: 4px solid #ff9900;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    .news-card {
        background-color: #161a25;
        padding: 12px;
        border-radius: 6px;
        border-left: 3px solid #3498db;
        margin-bottom: 8px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #121620;
        border: 1px solid #232936;
        padding: 8px 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Lateral Workspace Sidebar Controller
st.sidebar.markdown("### 🛡️ Capital Defense Deck")
account_balance_zar = st.sidebar.number_input("Wallet Capital Base (ZAR)", min_value=10.0, value=500.00, step=50.0)
max_risk_allowed_pct = st.sidebar.slider("Maximum Trade Allocation Risk (%)", 1.0, 10.0, 5.0)

# ==================== GLOBAL FX MATRIX SEARCH ENGINE ====================
st.sidebar.markdown("### 🔍 FX Market Search Engine")
st.sidebar.caption("Format example: EURUSD=X, AUDUSD=X, EURZAR=X")
search_ticker = st.sidebar.text_input("Enter Ticker Symbol:", value="").strip().upper()
trigger_search = st.sidebar.button("⚡ Scan Asset Vector")

# ==================== ANALYTICS & HYPOTHESIS CALCULATORS ====================
def compile_market_signals(df_d, df_h):
    """Processes pricing data and calculates multi-indicator trend matrices."""
    df_h = df_h.copy()
    close_series = pd.Series(df_h['Close'].values.flatten())
    
    df_h['RSI'] = ta.momentum.RSIIndicator(close=close_series, window=14).rsi().fillna(50.0).values
    df_h['EMA_200'] = ta.trend.EMAIndicator(close=close_series, window=200).ema_indicator().fillna(close_series).values
    df_h['MACD_Hist'] = ta.trend.MACD(close=close_series).macd_diff().fillna(0.0).values
    df_h['ATR'] = ta.volatility.AverageTrueRange(high=df_h['High'], low=df_h['Low'], close=df_h['Close']).average_true_range().fillna(close_series * 0.002).values
    
    df_h['Recent_Low'] = df_h['Low'].rolling(window=24).min()
    df_h['Recent_High'] = df_h['High'].rolling(window=24).max()
    
    df_h['Signal'] = "HOLD"
    
    for i in range(len(df_h)):
        if i < 200: continue
        price = float(close_series.iloc[i])
        rsi = df_h['RSI'].iloc[i]
        ema = df_h['EMA_200'].iloc[i]
        hist = df_h['MACD_Hist'].iloc[i]
        
        if (rsi < 40 or hist > 0) and (price > ema):
            df_h.loc[df_h.index[i], 'Signal'] = "BUY"
        elif (rsi > 60 or hist < 0) and (price < ema):
            df_h.loc[df_h.index[i], 'Signal'] = "SELL"
            
    return df_h

def generate_market_hypothesis(ticker, latest, asset_name):
    """Generates structural market hypotheses using live technical positioning."""
    price = latest['Close']
    ema = latest['EMA_200']
    rsi = latest['RSI']
    
    if price > ema:
        bias = "BULLISH ACCUMULATION"
        action = f"Look for pullbacks toward the support baseline near R{ema:.2f} if trading locally." if "ZAR" in ticker else f"Look for buy confirmations above ${ema:.2f}."
    else:
        bias = "BEARISH DISTRIBUTION"
        action = f"Expect overhead ceiling selling pressure near the 200 EMA area."

    hypothesis = (
        f"🧭 **Macro Bias:** {bias} | **Current Momentum (RSI):** {rsi:.1f}\n\n"
        f"📊 **Market Hypothesis:** {asset_name} ({ticker}) is trading in a trend phase relative to its 200 hourly EMA line. "
        f"With the technical index sitting at {rsi:.1f}, conditions point to consolidation. {action}"
    )
    return hypothesis

def draw_advanced_chart(df, title_name):
    plot_df = df.tail(100)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="Candles"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA_200'], line=dict(color='#ff9900', width=1.5), name="200 EMA"))
    fig.update_layout(xaxis_rangeslider_visible=False, height=400, template="plotly_dark", paper_bgcolor="#0c0e14", plot_bgcolor="#0c0e14", margin=dict(l=10, r=10, t=30, b=10))
    return fig

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        try: return pd.read_csv(JOURNAL_FILE)
        except Exception: pass
    return pd.DataFrame(columns=["Timestamp", "Asset", "Type", "Direction", "Entry_Price", "SL", "TP", "Status", "Profit_Loss_ZAR"])

def log_trade(asset, trade_type, direction, entry, sl, tp, status="OPEN", pl=0.0):
    df = load_journal()
    new_row = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Asset": asset, "Type": trade_type, "Direction": direction, "Entry_Price": float(entry), "SL": float(sl), "TP": float(tp), "Status": status, "Profit_Loss_ZAR": float(pl)}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False)

# ==============================================================================
# 🏛️ WORKSPACE MATRIX CONTROL PANEL
# ==============================================================================
st.title("🛸 MARS_BOT V11.0: MASTER CORE CONTROL")
st.caption(f"🕒 Engine Core Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} SAST")

# Render Three Sheet Workspace Layout
tab_matrix, tab_news, tab_journal = st.tabs(["📊 TERMINAL SIGNALS", "📰 SATELLITE NEWS", "📓 LEDGER JOURNAL"])

try:
    current_usdzar = float(yf.Ticker("USDZAR=X").history(period="1mo", interval="1d")['Close'].iloc[-1])
except Exception:
    current_usdzar = 18.35

st.sidebar.metric("🇿🇦 Live USD/ZAR Reference", f"R{current_usdzar:.2f}")

# Core baseline watchlist
watchlists = {
    "USDZAR=X":  {"name": "US Dollar / SA Rand", "type": "FX_ZAR"},
    "GBPUSD=X":  {"name": "British Pound / US Dollar", "type": "FX"},
    "GC=F":      {"name": "Gold Ounce Futures", "type": "COMMODITY"},
    "^NDX":      {"name": "US Tech 100 (Nasdaq 100)", "type": "INDEX"}
}

# Dynamic implementation of user-searched assets into active memory desk
if trigger_search and search_ticker:
    if search_ticker not in watchlists:
        watchlists[search_ticker] = {"name": f"Searched Asset Vector ({search_ticker})", "type": "FX"}

# --- PROCESS TICKER DATA ONSHORE ---
analyzed_watchlists = {}
for ticker, asset in watchlists.items():
    try:
        feed = yf.Ticker(ticker)
        df_d = feed.history(period="3mo", interval="1d")
        df_h = feed.history(period="1mo", interval="1h")
        if not df_d.empty and not df_h.empty:
            analyzed_watchlists[ticker] = {
                "asset": asset,
                "df": compile_market_signals(df_d, df_h),
                "ticker_obj": feed
            }
    except Exception:
        if ticker == search_ticker:
            st.sidebar.error(f"❌ Could not isolate asset telemetry for symbol: {ticker}")
        continue

target_rrr = 2.0
atr_multiplier = 2.0

# ==================== SHEET 1: TERMINAL SIGNALS MATRIX ====================
with tab_matrix:
    if trigger_search and search_ticker in analyzed_watchlists:
        st.success(f"🎯 Vector Core focused on searched asset: {search_ticker}")
        
    st.markdown("### 📊 Active Vector Signals Matrix")
    for ticker, data in analyzed_watchlists.items():
        asset = data["asset"]
        df_analyzed = data["df"]
        latest = df_analyzed.iloc[-1]
        
        signal_text = "⏳ HOLD" if latest['Signal'] == "HOLD" else f"🔥 {latest['Signal']}"
        
        with st.expander(f"📦 {asset['name']} ({ticker}) — Status: {signal_text}"):
            chart_fig = draw_advanced_chart(df_analyzed, asset['name'])
            st.plotly_chart(chart_fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Spot Price", f"R{latest['Close']:.4f}" if "ZAR" in ticker else f"${latest['Close']:.4f}" if asset["type"] == "FX" else f"${latest['Close']:.2f}")
                st.metric("RSI Oscillator", f"{latest['RSI']:.1f}")
            
            with col2:
                # Continuous calculations for parameter lines (Always visible on desk)
                sl_dist = float(latest['ATR']) * atr_multiplier
                stop_loss = float(latest['Close'] - sl_dist if latest['Signal'] != "SELL" else latest['Close'] + sl_dist)
                take_profit = float(latest['Close'] + (sl_dist * target_rrr) if latest['Signal'] != "SELL" else latest['Close'] - (sl_dist * target_rrr))
                
                mult = 10000 if asset["type"] in ["FX_ZAR", "FX"] else 1
                pts_sl = abs(latest['Close'] - stop_loss) * mult
                pts_tp = abs(take_profit - latest['Close']) * mult
                real_zar_risk = pts_sl * 0.10 if asset["type"] == "FX_ZAR" else (pts_sl * 0.01) * current_usdzar if asset["type"] == "FX" else (pts_sl * 0.10) * current_usdzar
                risk_pct = (real_zar_risk / account_balance_zar) * 100
                
                st.subheader("🎯 Live Parameter Setup")
                st.write(f"🛑 **Suggested SL:** {stop_loss:.4f} (`{pts_sl:.1f} pts away`)")
                st.write(f"🏁 **Suggested TP:** {take_profit:.4f} (`{pts_tp:.1f} pts away`)")
                st.write(f"🛡️ **Capital Exposure Risk:** R{real_zar_risk:.2f} ({risk_pct:.1f}% of capital)")
                
                if risk_pct > max_risk_allowed_pct:
