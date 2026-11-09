import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
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
st.set_page_config(page_title="MARS_BOT V12.0 Desk", page_icon="🛸", layout="wide")

# Persistent Session State Storage Core
if "watchlists" not in st.session_state:
    st.session_state.watchlists = {
        "USDZAR=X": {"name": "US Dollar / SA Rand", "type": "FX_ZAR"}
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

st.sidebar.markdown("### 🔍 Global Market Search Engine")
st.sidebar.caption("Type any symbol: e.g., EURUSD=X, GBPUSD=X, GC=F, BTC-USD, ^NDX")
search_ticker = st.sidebar.text_input("Enter Active Ticker Symbol:", value="").strip().upper()

# Core Functional Trigger for Adding More Searched Markets Safely
if st.sidebar.button("⚡ Scan Asset Vector") and search_ticker:
    if "ZAR" in search_ticker:
        determined_type = "FX_ZAR"
        friendly_name = f"US Dollar / SA Rand Cross ({search_ticker})" if "USD" in search_ticker else f"Rand Currency Pair ({search_ticker})"
    elif "=" in search_ticker:
        determined_type = "FX"
        friendly_name = f"Global FX Contract ({search_ticker})"
    elif "GC" in search_ticker or "=F" in search_ticker:
        determined_type = "COMMODITY"
        friendly_name = f"Commodity Futures Vector ({search_ticker})"
    elif "^" in search_ticker:
        determined_type = "INDEX"
        friendly_name = f"Global Stock Market Index ({search_ticker})"
    else:
        determined_type = "EQUITY"
        friendly_name = f"Public Equity Stock Asset ({search_ticker})"
        
    # Append the newly searched market cleanly into active state memory list
    st.session_state.watchlists[search_ticker] = {"name": friendly_name, "type": determined_type}
    st.sidebar.success(f"🎯 Linked {search_ticker} to Active Desk Matrix!")

# Button to let you clear out the list and start fresh with a single search
if st.sidebar.button("🗑️ Reset Workspace Matrix"):
    st.session_state.watchlists = {"USDZAR=X": {"name": "US Dollar / SA Rand", "type": "FX_ZAR"}}
    st.rerun()

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
        ema = df_h['EMA_200'].iloc[i]
        hist = df_h['MACD_Hist'].iloc[i]
        
        if (rsi < 45 or hist > 0) and (price > ema):
            df_h.loc[df_h.index[i], 'Signal'] = "BUY"
        elif (rsi > 55 or hist < 0) and (price < ema):
            df_h.loc[df_h.index[i], 'Signal'] = "SELL"
    return df_h

def draw_advanced_chart(df, title_name):
    plot_df = df.tail(100)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="Candles"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA_200'], line=dict(color='#ff9900', width=1.5), name="200 EMA"))
    fig.update_layout(xaxis_rangeslider_visible=False, height=420, template="plotly_dark", paper_bgcolor="#0c0e14", plot_bgcolor="#0c0e14", margin=dict(l=10, r=10, t=30, b=10))
    return fig

try:
    current_usdzar = float(yf.Ticker("USDZAR=X").history(period="1mo", interval="1d")['Close'].iloc[-1])
except Exception:
    current_usdzar = 18.35
st.sidebar.metric("🇿🇦 Live USD/ZAR Reference", f"R{current_usdzar:.2f}")

tab_matrix, tab_news, tab_journal = st.tabs(["📊 TERMINAL SIGNALS", "📰 SATELLITE NEWS", "📓 LEDGER JOURNAL"])

# Data Processing Framework
analyzed_watchlists = {}
for ticker, asset in st.session_state.watchlists.items():
    try:
        feed = yf.Ticker(ticker)
        df_d = feed.history(period="3mo", interval="1d")
        df_h = feed.history(period="1mo", interval="1h")
        if not df_d.empty and not df_h.empty:
            analyzed_watchlists[ticker] = {"asset": asset, "df": compile_market_signals(df_d, df_h), "ticker_obj": feed}
    except Exception: continue

# ==================== SHEET 1: TERMINAL SIGNALS MATRIX ====================
with tab_matrix:
    st.markdown("### 📊 Active Vector Signals Matrix")
    for ticker, data in analyzed_watchlists.items():
        asset, df_analyzed = data["asset"], data["df"]
        latest = df_analyzed.iloc[-1]
        signal_text = "⏳ HOLD" if latest['Signal'] == "HOLD" else f"🔥 {latest['Signal']}"
        
        with st.expander(f"📦 {asset['name']} — Status: {signal_text}"):
            st.plotly_chart(draw_advanced_chart(df_analyzed, asset['name']), use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Active Price Spot", f"R{latest['Close']:.4f}" if "ZAR" in ticker else f"${latest['Close']:.4f}" if asset["type"] == "FX" else f"${latest['Close']:.2f}")
                st.metric("RSI Oscillator", f"{latest['RSI']:.1f}")
            with col2:
                sl_dist = float(latest['ATR']) * 2.0
                stop_loss = float(latest['Close'] - sl_dist if latest['Signal'] != "SELL" else latest['Close'] + sl_dist)
                take_profit = float(latest['Close'] + (sl_dist * 2.0) if latest['Signal'] != "SELL" else latest['Close'] - (sl_dist * 2.0))
                mult = 10000 if asset["type"] in ["FX_ZAR", "FX"] else 1
                pts_sl = abs(latest['Close'] - stop_loss) * mult
                
                if asset["type"] == "FX_ZAR":
                    real_zar_risk = pts_sl * 0.10
                elif asset["type"] == "FX":
                    real_zar_risk = (pts_sl * 0.01) * current_usdzar
                else:
                    real_zar_risk = (pts_sl * 0.10) * current_usdzar
                    
                risk_pct = (real_zar_risk / account_balance_zar) * 100
                
                st.subheader("🎯 Live Parameter Setup")
                st.write(f"🛑 **Suggested SL Price:** {stop_loss:.4f} (`{pts_sl:.1f} pts away`)")
                st.write(f"🏁 **Suggested TP Price:** {take_profit:.4f}")
                st.write(f"🛡️ **Capital Exposure Risk:** R{real_zar_risk:.2f} ({risk_pct:.1f}% of capital)")
                
                if risk_pct > max_risk_allowed_pct:
                    st.error("⚠️ RISK WARNING: Exposure parameters exceed safe limits. Skip entry execution.")
                else:
                    st.success("✅ RISK APPROVED: Asset conditions match small account scaling metrics.")

# ==================== SHEET 2: LINKED SATELLITE MODULE ====================
with tab_news:
    if modules_ready:
        news.render_news_tab(analyzed_watchlists)
    else:
        st.info("Syncing satellite modules...")

# ==================== SHEET 3: LINKED LEDGER MODULE ====================
with tab_journal:
    if modules_ready:
        journal.render_journal_tab(st.session_state.watchlists, current_usdzar)
    else:
        st.info("Syncing transaction modules...")
