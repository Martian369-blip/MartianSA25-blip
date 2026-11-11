import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import urllib.request
import ssl
import json
import datetime

# Bypass Streamlit Cloud SSL certificate blocks
ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(page_title="MARS_BOT V24 Live", page_icon="🛸", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>.block-container{padding-top:2.8rem;}</style>", unsafe_allow_html=True)

st.sidebar.markdown("### 🛡️ ZAR Wallet")
bal_zar = st.sidebar.number_input("Manual Balance (ZAR)", value=1013.84, step=50.0)
risk_pct = st.sidebar.slider("Max Risk (%)", 0.5, 10.0, 1.5, 0.5)
risk_zar = bal_zar * (risk_pct / 100.0)

st.markdown("### 🛸 MARS_BOT V24 Sovereign Desk")

assets = {
    "GBP/USD": ("GBP", "USD", "GBPUSD=X"),
    "AUD/USD": ("AUD", "USD", "AUDUSD=X"),
    "EUR/USD": ("EUR", "USD", "EURUSD=X"),
    "USD/JPY": ("USD", "JPY", "USDJPY=X"),
    "USD/ZAR": ("USD", "ZAR", "USDZAR=X"),
    "GBP/ZAR": ("GBP", "ZAR", "GBPZAR=X"),
    "EUR/ZAR": ("EUR", "ZAR", "EURZAR=X"),
    "Gold (XAU)": ("XAU", "USD", "GC=F"),
    "BTC/USD": ("BTC", "USD", "BTC-USD"),
    "ETH/USD": ("ETH", "USD", "ETH-USD"),
    "SOL/USD": ("SOL", "USD", "SOL-USD"),
}

c1, c2, c3 = st.columns([0.45, 0.35, 0.20])
pair_name = c1.selectbox("Pair", list(assets.keys()), label_visibility="collapsed")
tf = c2.selectbox("Timeframe", ["5m Scalp", "15m Intraday", "1H Swing", "Daily"], index=2, label_visibility="collapsed")
c3.button("🛰️ SCAN", use_container_width=True)

base, quote, y_sym = assets[pair_name]
tf_map = {"5m Scalp": ("5m", "5d"), "15m Intraday": ("15m", "5d"), "1H Swing": ("1h", "1mo"), "Daily": ("1d", "6mo")}
interval, rng = tf_map[tf]

def extract_closes(df):
    if df is None or df.empty:
        return pd.Series(dtype=float)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if "Close" in df.columns:
        s = df["Close"]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return pd.to_numeric(s, errors="coerce").dropna()
    return pd.Series(dtype=float)

def get_usdzar():
    try:
        s = extract_closes(yf.download("USDZAR=X", period="5d", interval="1h", progress=False))
        if not s.empty:
            return float(s.iloc[-1])
    except Exception:
        pass
    return 18.20

def get_candles():
    errors = []
    # Method 1: yfinance download (same engine your v1 app used)
    try:
        s = extract_closes(yf.download(y_sym, period=rng, interval=interval, progress=False))
        if len(s) > 15:
            return s, "yfinance Live", ""
        errors.append("yf.download empty")
    except Exception as e:
        errors.append(f"yf.download: {e}")

    # Method 2: yfinance Ticker history
    try:
        s = extract_closes(yf.Ticker(y_sym).history(period=rng, interval=interval))
        if len(s) > 15:
            return s, "yf.Ticker Live", ""
        errors.append("yf.Ticker empty")
    except Exception as e:
        errors.append(f"yf.Ticker: {e}")

    # Method 3: SSL-unlocked Yahoo v8 JSON
    try:
        ctx = ssl._create_unverified_context()
        url = f"https://yahoo.com{y_sym}?range={rng}&interval={interval}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=8, context=ctx).read().decode()
        data = json.loads(raw)
        res = data["chart"]["result"].pop(0)
        closes = [float(c) for c in res["indicators"]["quote"].pop(0)["close"] if c is not None]
        if len(closes) > 15:
            return pd.Series(closes), "Yahoo Direct SSL", ""
        errors.append("Yahoo JSON empty")
    except Exception as e:
        errors.append(f"Yahoo JSON: {e}")

    # Method 4: SSL-unlocked Frankfurter FX
    try:
        ctx = ssl._create_unverified_context()
        start = datetime.date.today() - datetime.timedelta(days=120)
        url = f"https://frankfurter.app{start}..{datetime.date.today()}?from={base}&to={quote}"
        raw = urllib.request.urlopen(url, timeout=8, context=ctx).read().decode()
        rates = json.loads(raw)["rates"]
        closes = [float(v[quote]) for _, v in sorted(rates.items()) if quote in v]
        if len(closes) > 15:
            return pd.Series(closes), "Frankfurter FX Live", ""
        errors.append("Frankfurter empty")
    except Exception as e:
        errors.append(f"Frankfurter: {e}")

    return pd.Series(dtype=float), "Offline", " | ".join(errors)

closes, src, err_log = get_candles()
usdzar = get_usdzar()

if closes.empty:
    st.error("Connection blocked by server. Exact reason below:")
    st.code(err_log)
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
    dec = 2 if base in ["BTC", "ETH", "SOL", "XAU"] else (3 if quote == "JPY" else 5)

    st.markdown(f"<div style='background:{col};padding:14px;border-radius:8px;color:white;text-align:center;font-weight:bold;font-size:1.2rem;'>{sig}</div>", unsafe_allow_html=True)
    st.caption(f"📡 Feed: **{src}** | USD/ZAR: **{usdzar:.2f}** | Risk Budget: **R{risk_zar:.2f}**")

    m1, m2, m3 = st.columns(3)
    m1.metric("Spot Price", f"{price:.{dec}f}")
    m2.metric("RSI (14)", f"{rsi:.1f}")
    m3.metric("Rec. Size", f"{lots:.2f} lots")

    k1, k2 = st.columns(2)
    k1.error(f"🛑 SL: `{sl:.{dec}f}`")
    k2.success(f"🎯 TP: `{tp:.{dec}f}`")

    st.line_chart(closes.tail(50))
