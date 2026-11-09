import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import os
import plotly.graph_objects as go
from datetime import datetime

# ==============================================================================
# 🛰️ RESILIENT MULTI-FILE ARCHITECTURE INTERLOCK (DYNAMIC IMPORT LAYER)
# ==============================================================================
try:
    import design_theme as theme
    import research_engine as engine
    modules_imported = True
except (ImportError, SyntaxError) as e:
    modules_imported = False
    st.sidebar.warning("⚠️ Core Engine Module Syncing... Using Standby Architecture Core.")

# --- STANDBY BACKUP LOGIC INJECTORS (Runs only if modular files are unreadable) ---
JOURNAL_FILE = "trading_journal.csv"

def backup_compile_market_signals(df_d, df_h):
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
        if (df_h['RSI'].iloc[i] < 35) and (price > df_h['EMA_200'].iloc[i]) and (df_h['MACD_Hist'].iloc[i] > 0):
            df_h.loc[df_h.index[i], 'Signal'] = "BUY"
        elif (df_h['RSI'].iloc[i] > 65) and (price < df_h['EMA_200'].iloc[i]) and (df_h['MACD_Hist'].iloc[i] < 0):
            df_h.loc[df_h.index[i], 'Signal'] = "SELL"
    return df_h

def backup_draw_advanced_chart(df, title_name):
    plot_df = df.tail(100)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name="Candles"))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['EMA_200'], line=dict(color='#ff9900', width=1.5), name="200 EMA"))
    fig.update_layout(xaxis_rangeslider_visible=False, height=400, template="plotly_dark", paper_bgcolor="#0c0e14", plot_bgcolor="#0c0e14")
    return fig

def backup_load_journal():
    if os.path.exists(JOURNAL_FILE):
        try: return pd.read_csv(JOURNAL_FILE)
        except Exception: pass
    return pd.DataFrame(columns=["Timestamp", "Asset", "Type", "Direction", "Entry_Price", "SL", "TP", "Status", "Profit_Loss_ZAR"])

def backup_log_trade(asset, trade_type, direction, entry, sl, tp, status="OPEN", pl=0.0):
    df = backup_load_journal()
    new_row = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Asset": asset, "Type": trade_type, "Direction": direction, "Entry_Price": float(entry), "SL": float(sl), "TP": float(tp), "Status": status, "Profit_Loss_ZAR": float(pl)}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False)

# ==============================================================================
# 🏛️ WORKSPACE WORKFLOW LAYER
# ==============================================================================
st.set_page_config(page_title="MARS_BOT V10.0 Desk", page_icon="🛸", layout="wide")

st.markdown("<style>.stTabs [data-baseweb='tab'] { padding: 10px 20px; }</style>", unsafe_allow_html=True)

st.title("🛸 MARS_BOT V10.0: MASTER ANALYSIS DESK")
st.caption(f"🕒 Engine Core Synchronization: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} SAST")

if modules_imported:
    account_balance_zar, max_risk_allowed_pct = theme.render_small_account_header(balance=500.00, risk_pct=5.0)
else:
    st.sidebar.markdown("### 🛡️ Capital Defense Deck")
    account_balance_zar = st.sidebar.number_input("Wallet Capital Base (ZAR)", min_value=10.0, value=500.00, step=50.0)
    max_risk_allowed_pct = st.sidebar.slider("Maximum Trade Allocation Risk (%)", 1.0, 10.0, 5.0)

tab_matrix, tab_journal = st.tabs(["📊 LIVE TRADING MATRIX", "📓 LITIGATION JOURNAL"])

try:
    current_usdzar = float(yf.Ticker("USDZAR=X").history(period="1mo", interval="1d")['Close'].iloc[-1])
except Exception:
    current_usdzar = 18.35

st.sidebar.metric("🇿🇦 Live USD/ZAR Reference", f"R{current_usdzar:.2f}")

watchlists = {
    "USDZAR=X":  {"name": "US Dollar / SA Rand", "type": "FX_ZAR"},
    "GBPUSD=X":  {"name": "British Pound / US Dollar", "type": "FX"},
    "GC=F":      {"name": "Gold Ounce Futures", "type": "COMMODITY"},
    "^NDX":      {"name": "US Tech 100 (Nasdaq 100)", "type": "INDEX"}
}

# --- TAB 1: WORKSPACE MATRIX VIEW ---
with tab_matrix:
    st.markdown("### 📊 Live Analytics Matrix")
    for ticker, asset in watchlists.items():
        try:
            feed = yf.Ticker(ticker)
            df_d = feed.history(period="3mo", interval="1d")
            df_h = feed.history(period="1mo", interval="1h")
            
            if df_d.empty or df_h.empty: continue
            
            if modules_imported:
                df_analyzed = engine.compile_market_signals(df_d, df_h)
            else:
                df_analyzed = backup_compile_market_signals(df_d, df_h)
                
            latest = df_analyzed.iloc[-1]
            signal_text = "⏳ HOLD" if latest['Signal'] == "HOLD" else f"🔥 {latest['Signal']}"
            
            with st.expander(f"📦 {asset['name']} ({ticker}) — Status: {signal_text}"):
                if modules_imported:
                    chart_fig = theme.draw_advanced_chart(df_analyzed, asset['name'])
                else:
                    chart_fig = backup_draw_advanced_chart(df_analyzed, asset['name'])
                    
                st.plotly_chart(chart_fig, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Spot Price", f"R{latest['Close']:.4f}" if "ZAR" in ticker else f"${latest['Close']:.2f}")
                    st.metric("RSI Oscillator", f"{latest['RSI']:.1f}")
                
                with col2:
                    if latest['Signal'] != "HOLD":
                        sl_dist = float(latest['ATR']) * 2.0
                        stop_loss = float(latest['Close'] - sl_dist if latest['Signal'] == "BUY" else latest['Close'] + sl_dist)
                        take_profit = float(latest['Close'] + (sl_dist * 2.0) if latest['Signal'] == "BUY" else latest['Close'] - (sl_dist * 2.0))
                        
                        mult = 10000 if asset["type"] in ["FX_ZAR", "FX"] else 1
                        pts_sl = abs(latest['Close'] - stop_loss) * mult
                        real_zar_risk = pts_sl * 0.10 if asset["type"] == "FX_ZAR" else (pts_sl * 0.01) * current_usdzar if asset["type"] == "FX" else (pts_sl * 0.10) * current_usdzar
                        risk_pct = (real_zar_risk / account_balance_zar) * 100
                        
                        st.subheader("🎯 Execution Parameters")
                        st.write(f"🛑 **SL Price:** {stop_loss:.4f} | 🏁 **TP Price:** {take_profit:.4f}")
                        st.write(f"🛡️ **Risk profile:** R{real_zar_risk:.2f} ({risk_pct:.1f}% exposure)")
                        
                        if st.button(f"📥 Log Bot Signal for {ticker}", key=f"bot_{ticker}"):
                            if modules_imported: engine.log_trade(ticker, "AUTOMATIC", latest['Signal'], latest['Close'], stop_loss, take_profit)
                            else: backup_log_trade(ticker, "AUTOMATIC", latest['Signal'], latest['Close'], stop_loss, take_profit)
                            st.success("Signal recorded to Ledger sheet!")
                    else:
                        st.caption("Market trending inside safe boundaries. No trade parameters triggered.")
        except Exception:
            continue

# --- TAB 2: JOURNAL SHEET WORKSPACE ---
with tab_journal:
    st.header("📓 Personal Transaction Ledger")
    with st.form("Manual Entry Ticket"):
        st.subheader("➕ Record a Manual Trade")
        c1, c2, c3 = st.columns(3)
        with c1:
            m_asset = st.selectbox("Select Asset", list(watchlists.keys()))
            m_dir = st.selectbox("Direction", ["BUY", "SELL"])
        with c2:
            m_entry = st.number_input("Entry Price", value=0.0, format="%.5f")
            m_sl = st.number_input("Stop Loss", value=0.0, format="%.5f")
        with c3:
            m_tp = st.number_input("Take Profit", value=0.0, format="%.5f")
            m_pl = st.number_input("Closed P&L (ZAR Amount)", value=0.0)
            
        m_status = st.selectbox("Position State", ["OPEN", "CLOSED"])
        if st.form_submit_button("💾 Commit Trade to Journal"):
            if modules_imported: engine.log_trade(m_asset, "MANUAL", m_dir, m_entry, m_sl, m_tp, m_status, m_pl)
            else: backup_log_trade(m_asset, "MANUAL", m_dir, m_entry, m_sl, m_tp, m_status, m_pl)
            st.success("Manual entry logged securely!")

    st.divider()
    st.subheader("📋 Historical Trade Ledger Sheet")
    journal_df = engine.load_journal() if modules_imported else backup_load_journal()
    
    if not journal_df.empty:
        st.dataframe(journal_df, use_container_width=True)
        closed_trades = journal_df[journal_df['Status'] == "CLOSED"]
        if not closed_trades.empty:
            total_win = len(closed_trades[closed_trades['Profit_Loss_ZAR'] > 0])
            win_rate = (total_win / len(closed_trades)) * 100
            st.metric("Win Rate Profile", f"{win_rate:.1f}%", f"Total Net return: R{closed_trades['Profit_Loss_ZAR'].sum():.2f}")
    else:
