import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import os
import plotly.graph_objects as go
from datetime import datetime

# --- CONNECT DEEP INTO SPECIALIZED MULTI-FILE TECHNIQUE MODULES ---
try:
    import satellite_news as news
    import ledger_journal as journal
    modules_ready = True
except (ImportError, SyntaxError):
    modules_ready = False

# --- Visual State Engine Configuration ---
st.set_page_config(page_title="MARS_BOT V12.5 Desk", page_icon="🛸", layout="wide")

if "watchlists" not in st.session_state:
    st.session_state.watchlists = {
        "USDZAR=X":  {"name": "US Dollar / SA Rand", "type": "FX_ZAR"},
        "GBPUSD=X":  {"name": "British Pound / US Dollar", "type": "FX"},
        "GC=F":      {"name": "Gold Ounce Futures", "type": "COMMODITY"},
        "^NDX":      {"name": "US Tech 100 (Nasdaq)", "type": "INDEX"}
    }

st.markdown("""
    <style>
    .metric-card { background-color: #121620; padding: 15px; border-radius: 10px; border: 1px solid #232936; margin-bottom: 10px; }
    .hypothesis-box { background-color: #1a1c24; padding: 15px; border-left: 4px solid #ff9900; border-radius: 4px; margin-bottom: 15px; }
    .news-card { background-color: #161a25; padding: 12px; border-radius: 6px; border-left: 3px solid #3498db; margin-bottom: 8px; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: #121620; border: 1px solid #232936; padding: 8px 16px; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 🛡️ Capital Defense Deck")
account_balance_zar = st.sidebar.number_input("Wallet Capital Base (ZAR)", min_value=10.0, value=500.00, step=50.0)
max_risk_allowed_pct = st.sidebar.slider("Maximum Trade Allocation Risk (%)", 1.0, 10.0, 5.0)

# ==================== THE EXPANDED 30+ GLOBAL MARKET CATALOG ====================
st.sidebar.markdown("### 🌐 Asset Hub Selector")

market_options = {
    # 🇿🇦 South African Currency Crosses (Forex Majors)
    "USDZAR=X": {"name": "US Dollar / SA Rand", "type": "FX_ZAR"},
    "EURZAR=X": {"name": "Euro / SA Rand Cross", "type": "FX_ZAR"},
    "GBPZAR=X": {"name": "British Pound / SA Rand Cross", "type": "FX_ZAR"},
    "AUDZAR=X": {"name": "Australian Dollar / SA Rand", "type": "FX_ZAR"},
    "JPYZAR=X": {"name": "Japanese Yen / SA Rand Cross", "type": "FX_ZAR"},
    
    # 🌍 Global Forex Majors
    "GBPUSD=X": {"name": "British Pound / US Dollar", "type": "FX"},
    "EURUSD=X": {"name": "Euro / US Dollar", "type": "FX"},
    "USDJPY=X": {"name": "US Dollar / Japanese Yen", "type": "FX"},
    "AUDUSD=X": {"name": "Australian Dollar / US Dollar", "type": "FX"},
    "USDCAD=X": {"name": "US Dollar / Canadian Dollar", "type": "FX"},
    
    # 🛢️ Expanded Global Commodities Suite
    "GC=F":     {"name": "Gold Ounce Futures", "type": "COMMODITY"},
    "SI=F":     {"name": "Silver Ounce Futures", "type": "COMMODITY"},
    "CL=F":     {"name": "Crude Oil (WTI Futures)", "type": "COMMODITY"},
    "BZ=F":     {"name": "Brent Crude Oil Futures", "type": "COMMODITY"},
    "PL=F":     {"name": "Platinum Futures", "type": "COMMODITY"},
    "HG=F":     {"name": "Copper Futures", "type": "COMMODITY"},
    "NG=F":     {"name": "Natural Gas Futures", "type": "COMMODITY"},
    
    # 🇿🇦 Johannesburg Stock Exchange (JSE Leaders)
    "SOL.JO":   {"name": "Sasol Limited (JSE)", "type": "EQUITY"},
    "FSR.JO":   {"name": "FirstRand Bank (JSE)", "type": "EQUITY"},
    "SBK.JO":   {"name": "Standard Bank Group (JSE)", "type": "EQUITY"},
    "ANG.JO":   {"name": "Anglogold Ashanti (JSE)", "type": "EQUITY"},
    "IMP.JO":   {"name": "Impala Platinum (JSE)", "type": "EQUITY"},
    
    # 🇺🇸 Wall Street Blue Chips & Crypto
    "AAPL":     {"name": "Apple Inc. (Wall Street)", "type": "EQUITY"},
    "NVDA":     {"name": "NVIDIA Corp (Wall Street)", "type": "EQUITY"},
    "TSLA":     {"name": "Tesla Motors (Wall Street)", "type": "EQUITY"},
    "BTC-USD":  {"name": "Bitcoin / US Dollar", "type": "EQUITY"},
    "ETH-USD":  {"name": "Ethereum / US Dollar", "type": "EQUITY"},
    
    # 📉 Macro Stock Indices
    "^NDX":     {"name": "US Tech 100 (Nasdaq)", "type": "INDEX"},
    "^DJI":     {"name": "Wall Street 30 (Dow Jones)", "type": "INDEX"},
    "^GSPC":    {"name": "S&P 500 Index (US Market)", "type": "INDEX"},
    "^J203.JO": {"name": "JSE All Share Index (SA)", "type": "INDEX"}
}

selected_ticker = st.sidebar.selectbox(
    "Choose Market Vector to Analyze:",
    options=list(market_options.keys()),
    format_func=lambda x: f"{market_options[x]['name']} ({x})"
)

active_asset = market_options[selected_ticker]

# ==================== ANALYTICS PROCESSING NODES ====================
def compile_market_signals(df_d, df_h):
    df_h = df_h.copy()
    close_series = pd.Series(df_h['Close'].values.flatten())
    df_h['RSI'] = ta.momentum.RSIIndicator(close=close_series, window=14).rsi().fillna(50.0).values
    df_h['EMA_200'] = ta.trend.EMAIndicator(close=close_series, window=200).ema_indicator().fillna(close_series).values
    df_h['MACD_Hist'] = ta.trend.MACD(close=close_series).macd_diff().fillna(0.0).values
    df_h['ATR'] = ta.volatility.AverageTrueRange(high=df_h['High'], low=df_h['Low'], close=df_h['Close']).average_true_range().fillna(close_series * 0.002).values
    df_h['Signal'] = "HOLD"
    
    for i in range(len(df_h)):
        if i < 200: continue
        price = float(close_series.iloc[i])
        rsi = df_h['RSI'].iloc[i]
        hist = df_h['MACD_Hist'].iloc[i]
        
        if (rsi < 45 or hist > 0) and (price > df_h['EMA_200'].iloc[i]):
            df_h.loc[df_h.index[i], 'Signal'] = "BUY"
        elif (rsi > 55 or hist < 0) and (price < df_h['EMA_200'].iloc[i]):
            df_h.loc[df_h.index[i], 'Signal'] = "SELL"
    return df_h

def draw_advanced_chart(df, title_name):
    """
    Generates a high-fidelity TradingView clone candlestick chart layout
    with right-hand side pricing orientation and float markers.
    """
    plot_df = df.tail(100)
    latest_price = float(plot_df['Close'].iloc[-1])
    
    fig = go.Figure()
    
    # 🕯️ 1. Draw High-Vis Candlesticks (TradingView Style Colors)
    fig.add_trace(go.Candlestick(
        x=plot_df.index, 
        open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'], 
        name="Candles",
        increasing_line_color='#26a69a', increasing_fill_color='#26a69a',
        decreasing_line_color='#ef5350', decreasing_fill_color='#ef5350'
    ))
    
    # 🟠 2. Overlay Smooth 200 EMA Line
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['EMA_200'],
        line=dict(color='#ff9800', width=1.5), 
        name="200 EMA"
    ))
    
    # 🚀 3. Plot Native TradingView Execution Badges
    buys = plot_df[plot_df['Signal'] == "BUY"]
    sells = plot_df[plot_df['Signal'] == "SELL"]
    
    # Buy Badges
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys['Low'] * 0.997, 
        mode='markers+text',
        text=["🟢 BUY"] * len(buys),
        textposition="bottom center",
        textfont=dict(color="#26a69a", size=10, family="Arial Black"),
        marker=dict(symbol='triangle-up', size=10, color='#26a69a'), 
        name="BUY Signal"
    ))
    
    # Sell Badges
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells['High'] * 1.003, 
        mode='markers+text',
        text=["🔴 SELL"] * len(sells),
        textposition="top center",
        textfont=dict(color="#ef5350", size=10, family="Arial Black"),
        marker=dict(symbol='triangle-down', size=10, color='#ef5350'), 
        name="SELL Signal"
    ))
    
    # 🎯 4. Inject Active TradingView Price Axis Line
    fig.add_hline(
        y=latest_price, 
        line_dash="dash", 
        line_color="#787b86", 
        line_width=1,
        annotation_text=f" Live: {latest_price:.4f}" if latest_price < 100 else f" Live: {latest_price:.2f}", 
        annotation_position="right",
        annotation_font=dict(size=11, color="#ffffff", family="Arial Black"),
        annotation_bgcolor="#26a69a" if plot_df['Close'].iloc[-1] >= plot_df['Open'].iloc[-1] else "#ef5350"
    )
    
    # 🎛️ 5. Clean Layout Metrics (Right Side Y-Axis Toggle Active)
    fig.update_layout(
        title=f"📊 {title_name} - MARS TELEMETRY HUB",
        xaxis_rangeslider_visible=False, 
        height=450,
        template="plotly_dark", 
        paper_bgcolor="#0c0e14", 
        plot_bgcolor="#0c0e14",
        margin=dict(l=10, r=70, t=40, b=10),
        hovermode="x unified",
        xaxis=dict(gridcolor="#1e222d", showgrid=True),
        yaxis=dict(gridcolor="#1e222d", showgrid=True, side="right")
    )
    
    return fig

try:
    current_usdzar = float(yf.Ticker("USDZAR=X").history(period="1mo", interval="1d")['Close'].iloc[-1])
except Exception:
    current_usdzar = 18.35
st.sidebar.metric("🇿🇦 Live USD/ZAR Reference", f"R{current_usdzar:.2f}")

tab_matrix, tab_news, tab_journal = st.tabs(["📊 TERMINAL SIGNALS", "📰 SATELLITE NEWS", "📓 LEDGER JOURNAL"])

analyzed_watchlist = {}
try:
    feed = yf.Ticker(selected_ticker)
    df_d = feed.history(period="3mo", interval="1d")
    df_h = feed.history(period="1mo", interval="1h")
    if not df_d.empty and not df_h.empty:
        analyzed_watchlist[selected_ticker] = {"asset": active_asset, "df": compile_market_signals(df_d, df_h), "ticker_obj": feed}
except Exception:
    st.error("⚠️ Error loading live technical data feeds.")

# ==================== SHEET 1: TERMINAL SIGNALS MATRIX ====================
with tab_matrix:
    st.markdown(f"### 📊 Active Vector Signal: {active_asset['name']}")
    if selected_ticker in analyzed_watchlist:
        data = analyzed_watchlist[selected_ticker]
        df_analyzed, latest = data["df"], data["df"].iloc[-1]
        signal_text = "⏳ HOLD" if latest['Signal'] == "HOLD" else f"🔥 {latest['Signal']}"
        
        st.markdown(f"**Current Status Horizon:** {signal_text}")
