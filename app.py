import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Import our brand new specialized architectural layers
import design_theme as theme
import research_engine as engine

theme.apply_martian_theme()

st.title("🛸 MARS_BOT V9.5: ADVANCED INTERMARKET NETWORK")
st.caption(f"🕒 Engine Core Synchronization: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} SAST")

# Execute our specialized ZAR small account layout header module
account_balance_zar, max_risk_allowed_pct = theme.render_small_account_header(balance=500.00, risk_pct=5.0)

# Fetch baseline currency metrics
try:
    current_usdzar = float(yf.Ticker("USDZAR=X").history(period="1mo", interval="1d")['Close'].iloc[-1])
except Exception:
    current_usdzar = 18.35

st.sidebar.metric("🇿🇦 Live USD/ZAR Reference", f"R{current_usdzar:.2f}")

watchlists = {
    "USDZAR=X":  {"name": "US Dollar / SA Rand", "type": "FX_ZAR"},
    "GBPUSD=X":  {"name": "British Pound / US Dollar", "type": "FX"},
    "GC=F":      {"name": "Gold Ounce Futures", "type": "COMMODITY"},
    "^DJI":      {"name": "Wall Street 30 (Dow Jones)", "type": "INDEX"},
    "^NDX":      {"name": "US Tech 100 (Nasdaq 100)", "type": "INDEX"}
}

target_rrr = 2.0
atr_multiplier = 2.0

# 🏛️ Render main data cards
st.markdown("### 📊 Live Analytics Matrix")

for ticker, asset in watchlists.items():
    try:
        feed = yf.Ticker(ticker)
        df_d = feed.history(period="3mo", interval="1d")
        df_h = feed.history(period="1mo", interval="1h")

        if df_d.empty or df_h.empty:
            continue

        # Execute our broad research module
        metrics = engine.compile_market_signals(df_d, df_h)
        
        with st.expander(f"📦 {asset['name']} ({ticker}) — {metrics['signal']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Spot Price", f"R{metrics['price']:.4f}" if "ZAR" in ticker else f"${metrics['price']:.2f}")
                st.metric("Hourly RSI Filter", f"{metrics['hourly_rsi']:.1f}")
                
            with col2:
                st.metric("200 EMA Baseline", f"{metrics['hourly_ema']:.2f}")
                st.metric("MACD Histogram Pulse", f"{metrics['macd_hist']:.5f}")

            with col3:
                if metrics['direction'] != "HOLD":
                    sl_distance = metrics['hourly_atr'] * atr_multiplier
                    tp_distance = sl_distance * target_rrr
                    
                    stop_loss = metrics['price'] - sl_distance if metrics['direction'] == "LONG" else metrics['price'] + sl_distance
                    take_profit = metrics['price'] + tp_distance if metrics['direction'] == "LONG" else metrics['price'] - tp_distance
                    
                    mult = 10000 if asset["type"] in ["FX_ZAR", "FX"] else 1
                    pts_sl = abs(metrics['price'] - stop_loss) * mult
                    pts_tp = abs(take_profit - metrics['price']) * mult

                    if asset["type"] == "FX_ZAR":
                        real_zar_risk = pts_sl * 0.10
                        sl_fmt, tp_fmt = f"R{stop_loss:.4f}", f"R{take_profit:.4f}"
                    elif asset["type"] == "FX":
                        real_zar_risk = (pts_sl * 0.01) * current_usdzar
                        sl_fmt, tp_fmt = f"${stop_loss:.5f}", f"${take_profit:.5f}"
                    elif asset["type"] == "COMMODITY":
                        real_zar_risk = (pts_sl * 0.10) * current_usdzar
                        sl_fmt, tp_fmt = f"${stop_loss:.2f}", f"${take_profit:.2f}"
                    else:
                        real_zar_risk = (pts_sl * 0.05) * current_usdzar
                        sl_fmt, tp_fmt = f"${stop_loss:.2f}", f"${take_profit:.2f}"

                    risk_percentage = (real_zar_risk / account_balance_zar) * 100
                    
                    st.write(f"🛑 **Stop Loss Price:** {sl_fmt} (`{pts_sl:.1f} pts away`)")
                    st.write(f"🏁 **Take Profit Price:** {tp_fmt} (`{pts_tp:.1f} pts away`)")
                    st.divider()
                    st.write(f"💵 **Trade Risk:** R{real_zar_risk:.2f} ({risk_percentage:.1f}% exposure)")
                    
                    if risk_percentage > max_risk_allowed_pct:
                        st.error(f"⚠️ Sizing risks over your configured {max_risk_allowed_pct}% safety limit. SKIP!")
                    else:
                        st.success("✅ Risk parameters cleared for micro 0.01 allocation entry.")
                else:
                    st.info("Market vectors are currently balanced inside equilibrium channels. No active trade values found.")
                    
    except Exception as e:
        continue
