import streamlit as st
import pandas as pd
import os
from datetime import datetime

JOURNAL_FILE = "trading_journal.csv"

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        try:
            return pd.read_csv(JOURNAL_FILE)
        except Exception:
            pass
    return pd.DataFrame(columns=["Timestamp", "Asset", "Type", "Direction", "Entry_Price", "SL", "TP", "Status", "Profit_Loss_ZAR"])

def log_trade(asset, trade_type, direction, entry, sl, tp, status="OPEN", pl=0.0):
    df = load_journal()
    new_row = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Asset": asset, "Type": trade_type, "Direction": direction,
        "Entry_Price": float(entry), "SL": float(sl), "TP": float(tp), 
        "Status": status, "Profit_Loss_ZAR": float(pl)
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False)

def render_journal_tab(watchlists, current_usdzar):
    """Renders the ledger journal input cards and performance worksheets."""
    st.header("📓 Personal Transaction Ledger")
    
    with st.form("Manual Entry Ticket"):
        st.subheader("➕ Record a Manual Trade")
        c1, c2, c3 = st.columns(3)
        with c1:
            m_asset = st.selectbox("Select Asset Layout", list(watchlists.keys()))
            m_dir = st.selectbox("Direction", ["BUY", "SELL"])
        with c2:
            m_entry = st.number_input("Entry Price", value=0.0, format="%.5f")
            m_sl = m_entry * 0.99
            st.caption("Enter your baseline entries below to commit parameters safely")
        with c3:
            m_tp = m_entry * 1.02
            m_pl = st.number_input("Closed P&L (ZAR Amount)", value=0.0)
            
        m_status = st.selectbox("Position State", ["OPEN", "CLOSED"])
        if st.form_submit_button("💾 Commit Trade to Journal"):
            log_trade(m_asset, "MANUAL", m_dir, m_entry, m_sl, m_tp, m_status, m_pl)
            st.success("Manual entry logged securely!")

    st.divider()
    st.subheader("📋 Historical Trade Ledger Sheet")
    journal_df = load_journal()
    
    if journal_df.empty:
        st.info("Ledger clear. Commit manual positions to compile dashboard analytics.")
    else:
        st.dataframe(journal_df, use_container_width=True)
        closed_trades = journal_df[journal_df['Status'] == "CLOSED"]
        
        if not closed_trades.empty:
            total_win = len(closed_trades[closed_trades['Profit_Loss_ZAR'] > 0])
            win_rate = (total_win / len(closed_trades)) * 100
            st.metric("Win Rate Profile", f"{win_rate:.1f}%", f"Total Net return: R{closed_trades['Profit_Loss_ZAR'].sum():.2f}")
        else:
            st.info("No closed positions logged yet. Win rate metrics will populate once positions are finalized.")
