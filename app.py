import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

import design_theme as theme
import research_engine as engine

theme.apply_martian_theme()

st.title("🛸 MARS_BOT V10.0: MASTER ANALYSIS DESK")
account_balance_zar, max_risk_allowed_pct = theme.render_small_account_header(balance=500.00, risk_pct=5.0)

# Main Navigation Workspace
tab_matrix, tab_journal = st.tabs(["📊 LIVE TRADING MATRIX", "📓 LITIGATION JOURNAL"])

try:
    current_usdzar = float(yf.Ticker("USDZAR=X").history(period="1mo", interval="1d")['Close'].iloc[-1])
except Exception:
    current_usdzar = 18.35

watchlists = {
    "USDZAR=X":  {"name": "US Dollar / SA Rand", "type": "FX_ZAR"},
    "GBPUSD=X":  {"name": "British Pound / US Dollar", "type": "FX"},
    "GC=F":      {"name": "Gold Ounce Futures", "type": "COMMODITY"},
    "^NDX":      {"name": "US Tech 100 (Nasdaq 100)", "type": "INDEX"}
}

# ==================== TAB 1: LIVE CHARTING MATRIX ====================
with tab_matrix:
    for ticker, asset in watchlists.items():
        try:
            feed = yf.Ticker(ticker)
            df_d = feed.history(period="3mo", interval="1d")
            df_h = feed.history(period="1mo", interval="1h")
            
            if df_d.empty or df_h.empty: continue
                
            df_analyzed = engine.compile_market_signals(df_d, df_h)
            latest = df_analyzed.iloc[-1]
            
            signal_text = f"⏳ HOLD" if latest['Signal'] == "HOLD" else f"🔥 {latest['Signal']}"
            
            with st.expander(f"📦 {asset['name']} ({ticker}) — Status: {signal_text}"):
                # Render interactive high-res charting layer
                chart_fig = theme.draw_advanced_chart(df_analyzed, asset['name'])
                st.plotly_chart(chart_fig, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Spot Price", f"R{latest['Close']:.4f}" if "ZAR" in ticker else f"${latest['Close']:.2f}")
                    st.metric("RSI Oscillator", f"{latest['RSI']:.1f}")
                
                with col2:
                    if latest['Signal'] != "HOLD":
                        sl_dist = latest['ATR'] * 2.0
                        stop_loss = latest['Close'] - sl_dist if latest['Signal'] == "BUY" else latest['Close'] + sl_dist
                        take_profit = latest['Close'] + (sl_dist * 2.0) if latest['Signal'] == "BUY" else latest['Close'] - (sl_dist * 2.0)
                        
                        mult = 10000 if asset["type"] in ["FX_ZAR", "FX"] else 1
                        pts_sl = abs(latest['Close'] - stop_loss) * mult
                        
                        real_zar_risk = pts_sl * 0.10 if asset["type"] == "FX_ZAR" else (pts_sl * 0.01) * current_usdzar if asset["type"] == "FX" else (pts_sl * 0.10) * current_usdzar
                        risk_pct = (real_zar_risk / account_balance_zar) * 100
                        
                        st.subheader("🎯 Execution Parameters")
                        st.write(f"🛑 **SL:** {stop_loss:.4f} | 🏁 **TP:** {take_profit:.4f}")
                        st.write(f"🛡️ **Risk profile:** R{real_zar_risk:.2f} ({risk_pct:.1f}% exposure)")
                        
                        if st.button(f"📥 Log Bot Signal for {ticker}", key=f"bot_{ticker}"):
                            engine.log_trade(ticker, "AUTOMATIC", latest['Signal'], latest['Close'], stop_loss, take_profit)
                            st.success("Signal recorded to Ledger sheet!")
                    else:
                        st.caption("Market trending inside safe parameters. No target anomalies detected.")
        except Exception:
            continue

# ==================== TAB 2: TRADING JOURNAL DESK ====================
with tab_journal:
    st.header("📓 Personal Transaction Ledger")
    
    # Manual Entry Interface Module
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
        # Display aggregate ledger statistics
        closed_trades = journal_df[journal_df['Status'] == "CLOSED"]
        if not closed_trades.empty:
            total_win = len(closed_trades[closed_trades['Profit_Loss_ZAR'] > 0])
            win_rate = (total_win / len(closed_trades)) * 100
            st.metric("Win Rate Profile", f"{win_rate:.1f}%", f"Total Net return: R{closed_trades['Profit_Loss_ZAR'].sum():.2f}")
    else:
        st.info("Ledger clear. Commit manual execution positions or bot logs to compile statistics.")
