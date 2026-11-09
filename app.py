import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURATION ENGINE ---
st.set_page_config(page_title="MARS_BOT V9.0 Desk", page_icon="🛸", layout="wide")

def calculate_rsi(df, window=14):
    close_series = pd.Series(df['Close'].values.flatten())
    delta = close_series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0).values

def calculate_ema(df, window=200):
    close_series = pd.Series(df['Close'].values.flatten())
    return close_series.ewm(span=window, adjust=False).mean().values

def extract_hourly_atr(df_hourly, window=14):
    high = df_hourly['High'].values.flatten()
    low = df_hourly['Low'].values.flatten()
    close = df_hourly['Close'].values.flatten()
    high_low = high - low
    atr_series = pd.Series(high_low).rolling(window).mean()
    atr = atr_series.iloc[-1]
    return atr if not pd.isna(atr) else close[-1] * 0.002

# --- USER INTERFACE DESIGN ---
st.title("🛸 MARS_BOT V9.0: SOVEREIGN RISK DESK")
st.caption(f"🕒 System Live Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} SAST")

# Sidebar Account Controller Matrix
st.sidebar.header("🛡️ Risk Parameters")
account_balance_zar = st.sidebar.number_input("Account Balance (ZAR):", min_value=10.0, value=500.00, step=50.0)
max_risk_allowed_pct = st.sidebar.slider("Max Allowed Risk per Trade (%):", 1.0, 10.0, 5.0)

target_rrr = 2.0         
atr_multiplier = 2.0     

# Global Variables
try:
    usdzar_feed = yf.Ticker("USDZAR=X").history(period="1mo", interval="1d")
    current_usdzar = float(usdzar_feed['Close'].iloc[-1].iloc if isinstance(usdzar_feed['Close'].iloc[-1], pd.Series) else usdzar_feed['Close'].iloc[-1])
except Exception:
    current_usdzar = 18.35

st.sidebar.metric("🇿🇦 USD/ZAR Rate", f"R{current_usdzar:.2f}")

watchlists = {
    "USDZAR=X":  {"name": "US Dollar / SA Rand", "type": "FX_ZAR"},
    "GBPUSD=X":  {"name": "British Pound / US Dollar", "type": "FX"},
    "GC=F":      {"name": "Gold Ounce Futures", "type": "COMMODITY"},
    "^DJI":      {"name": "Wall Street 30 (Dow Jones)", "type": "INDEX"},
    "^NDX":      {"name": "US Tech 100 (Nasdaq 100)", "type": "INDEX"},
    "^GDAXI":    {"name": "Germany 40 (DAX Index)", "type": "INDEX"}
}

# --- MATRIX PROCESSING LOOP ---
for ticker, asset in watchlists.items():
    try:
        feed = yf.Ticker(ticker)
        df_d = feed.history(period="3mo", interval="1d")
        df_h = feed.history(period="1mo", interval="1h")

        if df_d.empty or df_h.empty:
            continue

        rsi_d = calculate_rsi(df_d)
        rsi_h = calculate_rsi(df_h)
        ema_h = calculate_ema(df_h, window=200)

        price = float(df_d['Close'].iloc[-1].iloc if isinstance(df_d['Close'].iloc[-1], pd.Series) else df_d['Close'].iloc[-1])
        hourly_rsi = float(rsi_h[-1])
        hourly_ema = float(ema_h[-1])
        hourly_atr = float(extract_hourly_atr(df_h))

        recent_low = float(df_h['Low'].tail(24).min().iloc if isinstance(df_h['Low'].tail(24).min(), pd.Series) else df_h['Low'].tail(24).min())
        recent_high = float(df_h['High'].tail(24).max().iloc if isinstance(df_h['High'].tail(24).max(), pd.Series) else df_h['High'].tail(24).max())

        sl_distance = hourly_atr * atr_multiplier
        tp_distance = sl_distance * target_rrr

        is_uptrend = price > hourly_ema
        is_downtrend = price < hourly_ema

        if (hourly_rsi < 35 or (price <= (recent_low * 1.005))) and is_uptrend:
            signal = "🚀 EXECUTE BUY (GO LONG)"
            direction = "LONG"
            stop_loss = price - sl_distance
            take_profit = price + tp_distance
            status_color = "green"
        elif (hourly_rsi > 65 or (price >= (recent_high * 0.995))) and is_downtrend:
            signal = "💥 EXECUTE SELL SHORT (GO SHORT)"
            direction = "SHORT"
            stop_loss = price + sl_distance
            take_profit = price - tp_distance
            status_color = "red"
        else:
            signal = "⏳ HOLD POSITION / PRESERVE CASH"
            direction = "HOLD"
            status_color = "normal"

        # Structural UI Expansion Box
        with st.expander(f"📦 {asset['name']} ({ticker}) — Status: {signal}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Price", f"R{price:.4f}" if "ZAR" in ticker else f"${price:.2f}")
                st.metric("Hourly RSI (15M Matrix)", f"{hourly_rsi:.1f}")
            
            with col2:
                st.metric("200 EMA Trendline", f"{hourly_ema:.2f}")
                st.write(f"**Market Regime:** Above 200 EMA Baseline" if is_uptrend else "**Market Regime:** Below 200 EMA Baseline")

            if direction != "HOLD":
                mult = 10000 if asset["type"] in ["FX_ZAR", "FX"] else 1
                pts_sl = abs(price - stop_loss) * mult
                pts_tp = abs(take_profit - price) * mult

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

                with col3:
                    st.subheader("📲 Live Ticket Properties")
                    st.write(f"🛑 **Stop Price Line:** {sl_fmt} (`{pts_sl:.1f} pts away`)")
                    st.write(f"🏁 **Limit Target Line:** {tp_fmt} (`{pts_tp:.1f} pts away`)")
                    
                    st.divider()
                    st.write(f"🛡️ **Capital Guard Assessment (For a Small Account at 0.01 Lot):**")
                    st.write(f"💵 **Cash Risk Amount:** R{real_zar_risk:.2f}")
                    st.write(f"📉 **Account Exposure Profile:** {risk_percentage:.1f}%")

                    if risk_percentage > max_risk_allowed_pct:
                        st.error(f"⚠️ RISK WARNING: Volatility risks over your {max_risk_allowed_pct}% target limit. SKIP execution!")
                    else:
                        st.success("✅ RISK APPROVED: Asset structure safe for micro allocation entry.")
            else:
                with col3:
                    st.info("No active execution metrics. Volatility parameters sitting within fair value bounds.")
                    
    except Exception as e:
        continue
