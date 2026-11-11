import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import json
import datetime

st.set_page_config(page_title="MARS_BOT Live", page_icon="🛸", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>.block-container{padding-top:2.8rem;}</style>", unsafe_allow_html=True)

st.sidebar.markdown("### 🛡️ ZAR Wallet")
bal_zar = st.sidebar.number_input("Balance (ZAR)", value=1013.84, step=50.0)
risk_pct = st.sidebar.slider("Risk (%)", 0.5, 10.0, 1.5, 0.5)
risk_zar = bal_zar * (risk_pct / 100.0)

st.markdown("### 🛸 MARS_BOT V23 (Ultra-Light Mobile)")

assets = {
    "GBP/USD": ("GBP", "USD", "GBPUSD=X"),
    "EUR/USD": ("EUR", "USD", "EURUSD=X"),
    "AUD/USD": ("AUD", "USD", "AUDUSD=X"),
    "USD/ZAR": ("USD", "ZAR", "USDZAR=X"),
    "GBP/ZAR": ("GBP", "ZAR", "GBPZAR=X"),
    "BTC/USD": ("BTC", "USD", "BTC-USD"),
    "ETH/USD": ("ETH", "USD", "ETH-USD"),
    "SOL/USD": ("SOL", "USD", "SOL-USD"),
}

c1, c2, c3 = st.columns([0.45, 0.35, 0.20])
pair_name = c1.selectbox("Pair", list(assets.keys()), label_visibility="collapsed")
tf = c2.selectbox("Timeframe", ["5m Scalp", "15m Intraday", "1H Swing", "Daily"], label_visibility="collapsed")
c3.button("🛰️ SCAN", use_container_width=True)

base, quote, y_sym = assets[pair_name]
tf_map = {"5m Scalp": ("5m", "5d"), "15m Intraday": ("15m", "5d"), "1H Swing": ("1h", "1mo"), "Daily": ("1d", "6mo")}
interval, rng = tf_map[tf]

def get_usdzar():
    try:
        r = urllib.request.urlopen("https://frankfurter.dev", timeout=5)
        return float(json.loads(r.read().decode())["rates"]["ZAR"])
    except Exception:
        return 18.20

def get_candles():
    # Source 1: Yahoo Direct
    try:
        url = f"https://yahoo.com{y_sym}?range={rng}&interval={interval}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=6).read().decode())
        res = data["chart"]["result"].pop(0)
        closes = [c for c in res["indicators"]["quote"].pop(0)["close"] if c is not None]
        if len(closes) > 15:
            return pd.Series(closes), "Yahoo Live"
    except Exception:
        pass

    # Source 2: Coinbase Public Candles (Crypto)
    if base in ["BTC", "ETH", "SOL"]:
        try:
            gran = {"5m": 300, "15m": 900, "1h": 3600, "1d": 86400}[interval]
            url = f"https://coinbase.com{base}-{quote}/candles?granularity={gran}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            rows = json.loads(urllib.request.urlopen(req, timeout=6).read().decode())
            closes = [float(x[4]) for x in reversed(rows)]
            if len(closes) > 15:
                return pd.Series(closes), "Coinbase Live"
        except Exception:
            pass

    # Source 3: Frankfurter Central Bank FX (100% Unblockable)
    try:
        start = datetime.date.today() - datetime.timedelta(days=90)
        url = f"https://frankfurter.dev{start}..{datetime.date.today()}?base={base}&symbols={quote}"
        rates = json.loads(urllib.request.urlopen(url, timeout=6).read().decode())["rates"]
        closes = [float(v[quote]) for _, v in sorted(rates.items()) if quote in v]
        if len(closes) > 15:
            return pd.Series(closes), "ECB/Frankfurter FX Live"
    except Exception:
        pass

    return pd.Series(dtype=float), "Offline"

closes, src = get_candles()
usdzar = get_usdzar()

if closes.empty:
    st.error("All feeds offline. Check Streamlit Cloud internet/reboot.")
else:
    price = float(closes.iloc[-1])
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = float((100 - (100 / (1 + gain / (loss + 1e-9)))).iloc[-1])
    ema20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
    vol = float(closes.diff().abs().tail(14).mean()) or (price * 0.001)

    if price > ema20 > ema50 and rsi < 68:
        sig, col = "🚀 BUY / LONG (TREND ALIGNED)", "#2E7D32"
        sl, tp = price - (vol * 2.5), price + (vol * 4.5)
    elif price < ema20 < ema50 and rsi > 32:
        sig, col = "💥 SELL / SHORT (TREND ALIGNED)", "#C62828"
        sl, tp = price + (vol * 2.5), price - (vol * 4.5)
    elif rsi <= 30:
        sig, col = "⚠️ OVERSOLD BOUNCE WATCH (RSI < 30)", "#EF6C00"
        sl, tp = price - (vol * 2.0), price + (vol * 3.0)
    elif rsi >= 70:
        sig, col = "⚠️ OVERBOUGHT DROP WATCH (RSI > 70)", "#EF6C00"
        sl, tp = price + (vol * 2.0), price - (vol * 3.0)
    else:
        sig, col = "⏳ HOLD / WAIT FOR SETUP", "#546E7A"
        sl, tp = price - (vol * 2.0), price + (vol * 2.0)

    stop_dist = abs(price - sl)
    zar_per_lot = (stop_dist * 100000.0) if quote == "ZAR" else (stop_dist * 100000.0 * usdzar)
    lots = max(0.01, round(risk_zar / max(zar_per_lot, 1e-6), 2))
    dec = 2 if base in ["BTC", "ETH", "SOL"] else 5

    st.markdown(f"<div style='background:{col};padding:14px;border-radius:8px;color:white;text-align:center;font-weight:bold;font-size:1.2rem;'>{sig}</div>", unsafe_allow_html=True)
    st.caption(f"📡 Feed: **{src}** | USD/ZAR: **{usdzar:.2f}** | Budget: **R{risk_zar:.2f}**")

    m1, m2, m3 = st.columns(3)
    m1.metric("Spot Price", f"{price:.{dec}f}")
    m2.metric("RSI (14)", f"{rsi:.1f}")
    m3.metric("Rec. Size", f"{lots:.2f} lots")

    k1, k2 = st.columns(2)
    k1.error(f"🛑 SL: `{sl:.{dec}f}`")
    k2.success(f"🎯 TP: `{tp:.{dec}f}`")

    st.line_chart(closes.tail(50))
