import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Direct, clean compilation linkage to module sheets
import design_theme as theme
import research_engine as engine

# Execute web visual design module adjustments
st.set_page_config(page_title="MARS_BOT V10.0 Desk", page_icon="🛸", layout="wide")
theme.apply_martian_theme()

st.title("🛸 MARS_BOT V10.0: MASTER ANALYSIS DESK")
st.caption(f"🕒 Engine Core Synchronization: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} SAST")

# Render capital configuration parameters inside navigation dashboard
account_balance_zar, max_risk_allowed_pct = theme.render_small_account_header(balance=500.00, risk_pct=5.0)

tab_matrix, tab_journal = st.tabs(["📊 LIVE TRADING MATRIX", "📓 LITIGATION JOURNAL"])

try:
    usdzar_feed = yf.Ticker("USDZAR=X").history(period="1mo", interval="1d")
    current_usdzar = float(usdzar_feed['Close'].iloc[-1])
except Exception:
    current_usdzar = 18.35

st.sidebar.metric("🇿🇦 Live USD/ZAR Reference", f"R{current_usdzar:.2f}")

watchlists = {
    "USDZAR=X":  {"name": "US Dollar / SA Rand", "type": "FX_ZAR"},
    "GBPUSD=X":  {"name": "British Pound / US Dollar", "type": "FX"},
    "GC=F":      {"name": "Gold Ounce Futures", "type": "COMMODITY"},
    "^NDX":      {"name": "US Tech 100 (Nasdaq 100)", "type": "INDEX"}
}

target_rrr = 2.0
atr_multiplier = 2.0

# ==================== TAB 1: WORKSPACE MATRIX ====================
with tab_matrix:
    st.markdown("### 📊 Live Analytics Matrix")
    for ticker, asset in watchlists.items():
        try:
            feed = yf.Ticker(ticker)
            df_d = feed.history(period="3mo", interval="1d")
            df_h = feed.history(period="1mo", interval="1h")
            
            if df_d.empty or df_h.empty: 
                continue
                
            # Process historical matrix data through the research module sheet
            df_analyzed = engine.compile_market_signals(df_d, df_h)
            latest = df_analyzed.iloc[-1]
            
            signal_text = "⏳ HOLD" if latest['Signal'] == "HOLD" else f"🔥 {latest['Signal']}"
            
            with st.expander(f"📦 {asset['name']} ({ticker}) — Status: {signal_text}"):
                # Render Plotly interactive charting module natively
                chart_fig = theme.draw_advanced_chart(df_analyzed, asset['name'])
                st.plotly_chart(chart_fig, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Spot Price", f"R{latest['Close']:.4f}" if "ZAR" in ticker else f"${latest['Close']:.2f}")
                    st.metric("RSI Oscillator", f"{latest['RSI']:.1f}")
                
                with col2:
                    if latest['Signal'] != "HOLD":
                        sl_dist = float(latest['ATR']) * atr_multiplier
                        stop_loss = float(latest['Close'] - sl_dist if latest['Signal'] == "BUY" else latest['Close'] + sl_dist)
                        take_profit = float(latest['Close'] + (sl_dist * target_rrr) if latest['Signal'] == "BUY" else latest['Close'] - (sl_dist * target_rrr))
                        
                        mult = 10000 if asset["type"] in ["FX_ZAR", "FX"] else 1
                        pts_sl = abs(latest['Close'] - stop_loss) * mult
                        
                        if asset["type"] == "FX_ZAR":
                            real_zar_risk = pts_sl * 0.10
                        elif asset["type"] == "FX":
                            real_zar_risk = (pts_sl * 0.01) * current_usdzar
                        else:
                            real_zar_risk = (pts_sl * 0.10) * current_usdzar
                            
                        risk_pct = (real_zar_risk / account_balance_zar) * 100
                        
                        st.subheader("🎯 Execution Parameters")
                        st.write(f"🛑 **SL Price:** {stop_loss:.4f} | 🏁 **TP Price:** {take_profit:.4f}")
                        st.write(f"🛡️ **Risk profile:** R{real_zar_risk:.2f} ({risk_pct:.1f}% exposure)")
                        
                        if st.button(f"📥 Log Bot Signal for {ticker}", key=f"bot_{ticker}"):
                            engine.log_trade(ticker, "AUTOMATIC", latest['Signal'], latest['Close'], stop_loss, take_profit)
                            st.success("Signal recorded to Ledger sheet!")
                    else:
                        st.caption("Market trending inside safe boundaries. No trade parameters triggered.")
        except Exception as e:
            continue

# ==================== TAB 2: JOURNAL WORKSPACE ====================
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
            engine.log_trade(m_asset, "MANUAL", m_dir, m_entry, m_sl, m_tp, m_status, m_pl)
            st.success("Manual entry logged securely!")

    st.divider()
    st.subheader("📋 Historical Trade Ledger Sheet")
    journal_df = engine.load_journal()
    
    if not journal_df.empty:
        st.dataframe(journal_df, use_container_width=True)
        closed_trades = journal_df[journal_df['Status'] == "CLOSED"]
        if not closed_trades.empty:
            total_win = len(closed_trades[closed_trades['Profit_Loss_ZAR'] > 0])
            win_rate = (total_win / len(closed_trades)) * 100
            st.metric("Win Rate Profile", f"{win_rate:.1f}%", f"Total Net return: R{closed_trades['Profit_Loss_ZAR'].sum():.2f}")
    else:
        st.info("Ledger clear. Commit manual positions to compile dashboard analytics.")
