import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import urllib.request
import json
import datetime
import os

# ==================== 1. PAGE CONFIG & MOBILE UI ====================
st.set_page_config(
    page_title="MARS_BOT V22.1 Sovereign Desk",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .block-container { padding-top: 2.8rem; padding-bottom: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.35rem; }
    .signal-box {
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.3rem;
        margin-bottom: 12px;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

PERSISTENT_FILE = "ledger_vault.csv"

def load_persistent_ledger():
    if os.path.exists(PERSISTENT_FILE):
        try:
            df = pd.read_csv(PERSISTENT_FILE)
            if not df.empty:
                return df
        except Exception:
            return pd.DataFrame(columns=["Timestamp", "Asset", "Timeframe", "Action", "Price", "SL", "TP", "Lots", "RSI"])
    return pd.DataFrame(columns=["Timestamp", "Asset", "Timeframe", "Action", "Price", "SL", "TP", "Lots", "RSI"])

def save_persistent_ledger(df):
    df.to_csv(PERSISTENT_FILE, index=False)

if "journal_db" not in st.session_state:
    st.session_state["journal_db"] = load_persistent_ledger()

# ==================== 2. SIDEBAR: MANUAL ZAR CAPITAL & RISK ====================
st.sidebar.markdown("### 🛡️ Capital Defense Deck (ZAR)")
account_balance_zar = st.sidebar.number_input(
    "Manual Wallet Balance (ZAR)",
    min_value=50.0,
    value=1013.84,
    step=50.0,
    format="%.2f"
)
max_risk_allowed_pct = st.sidebar.slider(
    "Max Risk Per Trade (%)",
    min_value=0.5,
    max_value=10.0,
    value=1.5,
    step=0.5
)
max_risk_zar = account_balance_zar * (max_risk_allowed_pct / 100.0)
st.sidebar.info(f"💰 Max Risk Budget: **R{max_risk_zar:.2f}** per trade")

# ==================== 3. ASSET & TIMEFRAME CATALOG ====================
ig_name_map = {
    "GBPUSD=X": "GBP/USD (Cable)",
    "AUDUSD=X": "AUD/USD (Aussie)",
    "EURUSD=X": "EUR/USD (Fiber)",
    "USDJPY=X": "USD/JPY (Ninja)",
    "USDZAR=X": "USD/ZAR (US Dollar)",
    "EURZAR=X": "EUR/ZAR (Euro)",
    "GBPZAR=X": "GBP/ZAR (British Pound)",
    "AUDZAR=X": "AUD/ZAR (Aussie Dollar)",
    "JPYZAR=X": "JPY/ZAR (Japanese Yen)",
    "CADZAR=X": "CAD/ZAR (Canadian Dollar)",
    "CHFZAR=X": "CHF/ZAR (Swiss Franc)",
    "NZDZAR=X": "NZD/ZAR (Kiwi Dollar)",
    "USDCAD=X": "USD/CAD (Loonie)",
    "USDCHF=X": "USD/CHF (Swissie)",
    "NZDUSD=X": "NZD/USD (Kiwi)",
    "EURGBP=X": "EUR/GBP (Chunnel)",
    "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY (Guppy)",
    "GC=F":     "Gold (Ounce Futures)",
    "SI=F":     "Silver (Ounce Futures)",
    "PL=F":     "Platinum (Ounce Futures)",
    "PA=F":     "Palladium (Ounce Futures)",
    "CL=F":     "Crude Oil (WTI Futures)",
    "BZ=F":     "Brent Crude Oil Futures",
    "NG=F":     "Natural Gas Futures",
    "HG=F":     "Copper Futures",
    "BTC-USD":  "Bitcoin / US Dollar",
    "ETH-USD":  "Ethereum / US Dollar",
    "SOL-USD":  "Solana / US Dollar",
    "XRP-USD":  "Ripple / US Dollar",
    "^GSPC":    "S&P 500 Index (US Market)",
    "^NDX":     "NASDAQ 100 (US Tech)",
    "^DJI":     "Dow Jones Industrial 30",
    "^FTSE":    "FTSE 100 Index (London)",
    "^GDAXI":   "DAX Performance Index (Germany)",
    "^J203.JO": "JSE All Share Index (South Africa)",
    "SOL.JO":   "Sasol Ltd (JSE:SOL)",
    "FSR.JO":   "FirstRand Ltd (JSE:FSR)",
    "SBK.JO":   "Standard Bank Group (JSE:SBK)",
    "ANG.JO":   "Anglogold Ashanti (JSE:ANG)",
    "IMP.JO":   "Impala Platinum (JSE:IMP)",
    "NPN.JO":   "Naspers Ltd (JSE:NPN)",
    "AAPL":     "Apple Inc. (NASDAQ)",
    "NVDA":     "NVIDIA Corporation (NASDAQ)",
    "TSLA":     "Tesla Motors Inc. (NASDAQ)",
    "MSFT":     "Microsoft Corp. (NASDAQ)"
}

timeframe_configs = {
    "5m Scalp (Fast Intraday)":  {"entry_int": "5m",  "entry_per": "5d",  "macro_int": "1h", "macro_per": "1mo", "swing_bars": 12},
    "15m Intraday":              {"entry_int": "15m", "entry_per": "5d",  "macro_int": "1h", "macro_per": "1mo", "swing_bars": 10},
    "1H Swing":                  {"entry_int": "1h",  "entry_per": "1mo", "macro_int": "1d", "macro_per": "6mo", "swing_bars": 8},
    "4H Macro Trend":            {"entry_int": "1h",  "entry_per": "2mo", "macro_int": "1d", "macro_per": "1y",  "swing_bars": 16}
}

st.markdown("### 🛸 MARS_BOT V22.1 Sovereign Desk")

col_asset, col_tf, col_btn = st.columns([0.45, 0.35, 0.20])
display_options = list(ig_name_map.values())
reverse_map = {v: k for k, v in ig_name_map.items()}

with col_asset:
    chosen_display = st.selectbox("Asset", options=display_options, index=0, label_visibility="collapsed")
    selected_ticker = reverse_map[chosen_display]

with col_tf:
    selected_tf_label = st.selectbox("Timeframe", options=list(timeframe_configs.keys()), index=0, label_visibility="collapsed")
    tf_cfg = timeframe_configs[selected_tf_label]

with col_btn:
    scan_clicked = st.button("🛰️ SCAN", use_container_width=True)

# ==================== 4. ROCK-SOLID DATA ENGINE ====================
def clean_yf_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    required = ["Open", "High", "Low", "Close"]
    if not all(col in df.columns for col in required):
        return pd.DataFrame()
    return df[required].dropna()

def fetch_yahoo_direct(ticker, range_str, interval_str):
    encoded_ticker = urllib.request.quote(ticker)
    err_msg = "No data"
    for host in ["://yahoo.com", "://yahoo.com"]:
        url = f"https://{host}/v8/finance/chart/{encoded_ticker}?range={range_str}&interval={interval_str}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                res_list = raw.get("chart", {}).get("result")
                if not res_list:
                    continue
                first_res = res_list.pop(0)
                timestamps = first_res.get("timestamp", [])
                quote_list = first_res.get("indicators", {}).get("quote", [])
                if not timestamps or not quote_list:
                    continue
                quote = quote_list.pop(0)
                df = pd.DataFrame({
                    "Date": pd.to_datetime(timestamps, unit="s"),
                    "Open": quote.get("open"),
                    "High": quote.get("high"),
                    "Low": quote.get("low"),
                    "Close": quote.get("close")
                }).set_index("Date").dropna()
                if not df.empty:
                    return df, ""
        except Exception as e:
            err_msg = str(e)
    return pd.DataFrame(), err_msg

def fetch_frankfurter_v1(ticker, days=120):
    pair = ticker.replace("=X", "")
    if len(pair) != 6:
        return pd.DataFrame()
    base, quote = pair[:3], pair[3:]
    end_dt = datetime.date.today()
    start_dt = end_dt - datetime.timedelta(days=days)
    url = f"https://frankfurter.dev{start_dt}..{end_dt}?base={base}&symbols={quote}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            rates = json.loads(resp.read().decode("utf-8")).get("rates", {})
            rows = []
            for dt_str, val_dict in sorted(rates.items()):
                if quote in val_dict:
                    c = float(val_dict[quote])
                    rows.append({
                        "Date": pd.to_datetime(dt_str),
                        "Open": c,
                        "High": c * 1.0012,
                        "Low": c * 0.9988,
                        "Close": c
                    })
            if rows:
                return pd.DataFrame(rows).set_index("Date")
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()

def fetch_live_usdzar():
    df_zar, _ = fetch_yahoo_direct("USDZAR=X", "5d", "1h")
    if not df_zar.empty:
        return float(df_zar["Close"].iloc[-1])
    try:
        req = urllib.request.Request("https://frankfurter.devlatest?base=USD&symbols=ZAR", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return float(json.loads(resp.read().decode("utf-8"))["rates"]["ZAR"])
    except Exception:
        return 18.20

def get_market_data(ticker, entry_int, entry_per, macro_int, macro_per):
    logs = []
    df_entry, err1 = fetch_yahoo_direct(ticker, entry_per, entry_int)
    df_macro, err2 = fetch_yahoo_direct(ticker, macro_per, macro_int)
    if not df_entry.empty and not df_macro.empty:
        return df_entry, df_macro, "Yahoo Direct Live", ""
    logs.append(f"YahooDirect: {err1 or err2}")

    try:
        t = yf.Ticker(ticker)
        if df_entry.empty:
            df_entry = clean_yf_df(t.history(period=entry_per, interval=entry_int))
        if df_macro.empty:
            df_macro = clean_yf_df(t.history(period=macro_per, interval=macro_int))
        if not df_entry.empty and not df_macro.empty:
            return df_entry, df_macro, "yfinance Live", ""
        logs.append("yfinance: empty")
    except Exception as e:
        logs.append(f"yfinance: {e}")

