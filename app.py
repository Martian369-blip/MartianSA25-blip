import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go
from datetime import datetime

try:
    import satellite_news as news
    import ledger_journal as journal
    modules_ready = True
except (ImportError, SyntaxError):
    modules_ready = False

st.set_page_config(page_title="MARS_BOT V12.5 Desk", page_icon="🛸", layout="wide")

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
        if (df_h['RSI'].iloc[i] < 45 or df_h['MACD_Hist'].iloc[i] > 0) and (price > df_h['EMA_200'].iloc[i]):
            df_h.loc[df_h.index[i], 'Signal'] = "BUY"
        elif (df_h['RSI'].iloc[i] > 55 or df_h['MACD_Hist'].iloc[i] < 0) and (price < df_h['EMA_200'].iloc[i]):
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
        st.plotly_chart(draw_advanced_chart(df_analyzed, active_asset['name']), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Spot Price", f"R{latest['Close']:.4f}" if "ZAR" in selected_ticker or ".JO" in selected_ticker else f"${latest['Close']:.4f}" if active_asset["type"] == "FX" else f"${latest['Close']:.2f}")
            st.metric("RSI Oscillator", f"{latest['RSI']:.1f}")
        with col2:
            sl_dist = float(latest['ATR']) * 2.0
            stop_loss = float(latest['Close'] - sl_dist if latest['Signal'] != "SELL" else latest['Close'] + sl_dist)
            take_profit = float(latest['Close'] + (sl_dist * 2.0) if latest['Signal'] != "SELL" else latest['Close'] - (sl_dist * 2.0))
            mult = 10000 if active_asset["type"] in ["FX_ZAR", "FX"] else 1
            pts_sl = abs(latest['Close'] - stop_loss) * mult
            
            if active_asset["type"] == "FX_ZAR" or ".JO" in selected_ticker:
                real_zar_risk = pts_sl * 0.10
            elif active_asset["type"] == "FX":
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
        news.render_news_tab(analyzed_watchlist)
    else:
        st.info("Syncing satellite news modules...")

# ==================== SHEET 3: LINKED LEDGER MODULE ====================
with tab_journal:
    if modules_ready:
        ledger_map = {selected_ticker: active_asset}
        journal.render_journal_tab(ledger_map, current_usdzar)
    else:
        st.info("Syncing transaction ledger modules...")
