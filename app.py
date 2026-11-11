import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import os

# ==================== 1. PAGE CONFIG & MOBILE UI ====================
st.set_page_config(
    page_title="MARS_BOT V21.0 Sovereign Desk",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    .signal-box {
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.35rem;
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
            pass
    return pd.DataFrame(columns=["Timestamp", "Asset", "Timeframe", "Action", "Price", "SL", "TP", "Lots", "RSI"])

def save_persistent_ledger(df):
    df.to_csv(PERSISTENT_FILE, index=False)

# ==================== 2. SESSION STATE INITIALIZATION ====================
if "journal_db" not in st.session_state:
    st.session_state["journal_db"] = load_persistent_ledger()
if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None
if "last_scanned_key" not in st.session_state:
    st.session_state["last_scanned_key"] = ""

# ==================== 3. SIDEBAR: MANUAL ZAR CAPITAL & RISK ====================
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

# ==================== 4. ASSET & TIMEFRAME CATALOG ====================
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
    "15m Intraday":              {"entry_int": "15m", "entry_per": "10d", "macro_int": "1h", "macro_per": "2mo", "swing_bars": 10},
    "1H Swing":                  {"entry_int": "1h",  "entry_per": "1mo", "macro_int": "1d", "macro_per": "6mo", "swing_bars": 8},
    "4H Macro Trend":            {"entry_int": "1h",  "entry_per": "2mo", "macro_int": "1d", "macro_per": "1y",  "swing_bars": 16}
}

st.markdown("### 🛸 MARS_BOT V21.0 Sovereign Desk")

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

# ==================== 5. DATA FETCHING & TECHNICAL ENGINE ====================
def clean_yf_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    return df.dropna()

@st.cache_data(ttl=45)
def fetch_live_usdzar():
    try:
        fx = clean_yf_df(yf.download("USDZAR=X", period="2d", interval="1h", progress=False))
        if not fx.empty:
            return float(fx["Close"].iloc[-1])
    except Exception:
        pass
    return 18.20  # Fallback rate

@st.cache_data(ttl=30)
def fetch_market_frames(ticker, entry_int, entry_per, macro_int, macro_per):
    df_entry = clean_yf_df(yf.download(ticker, period=entry_per, interval=entry_int, progress=False))
    df_macro = clean_yf_df(yf.download(ticker, period=macro_per, interval=macro_int, progress=False))
    return df_entry, df_macro

def calculate_wilder_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    return 100.0 - (100.0 / (1.0 + rs))

def run_quant_engine(df_entry, df_macro, swing_bars, ticker, usdzar_rate, risk_zar):
    df_e = df_entry.copy()
    df_m = df_macro.copy()

    # 1. Higher-Timeframe Macro Trend Filter
    df_m["EMA_50"] = df_m["Close"].ewm(span=50, adjust=False).mean()
    macro_bullish = bool(df_m["Close"].iloc[-1] > df_m["EMA_50"].iloc[-1])

    # 2. Entry Timeframe Indicators
    df_e["RSI"] = calculate_wilder_rsi(df_e["Close"], 14).fillna(50.0)
    df_e["EMA_50"] = df_e["Close"].ewm(span=50, adjust=False).mean()
    df_e["EMA_200"] = df_e["Close"].ewm(span=200, adjust=False).mean()

    # ATR (14)
    hl = df_e["High"] - df_e["Low"]
    hc = np.abs(df_e["High"] - df_e["Close"].shift())
    lc = np.abs(df_e["Low"] - df_e["Close"].shift())
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df_e["ATR"] = tr.rolling(14).mean().bfill()

    # MACD
    ema12 = df_e["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df_e["Close"].ewm(span=26, adjust=False).mean()
    df_e["MACD"] = ema12 - ema26
    df_e["Signal_Line"] = df_e["MACD"].ewm(span=9, adjust=False).mean()
    df_e["MACD_Hist"] = df_e["MACD"] - df_e["Signal_Line"]

    # Bollinger Bands
    df_e["BB_Mid"] = df_e["Close"].rolling(20).mean()
    df_e["BB_Std"] = df_e["Close"].rolling(20).std()
    df_e["BB_High"] = df_e["BB_Mid"] + (df_e["BB_Std"] * 2)
    df_e["BB_Low"] = df_e["BB_Mid"] - (df_e["BB_Std"] * 2)

    latest = df_e.iloc[-1]
    prev = df_e.iloc[-2] if len(df_e) > 1 else latest

    price = float(latest["Close"])
    atr = float(latest["ATR"])
    rsi_now = float(latest["RSI"])
    rsi_prev = float(prev["RSI"])

    recent_floor = float(df_e["Low"].tail(swing_bars).min())
    recent_ceiling = float(df_e["High"].tail(swing_bars).max())

    # 3. Multi-Tier Signal Confluence Logic
    direction = "⏳ HOLD / STANDBY"
    color = "#546E7A"
    sl = 0.0
    tp = 0.0
    setup_note = "No high-probability confluence yet. Wait for pullback or momentum shift."

    # Tier A: High-Probability Trend Continuation
    if macro_bullish and price > latest["EMA_200"] and (rsi_now < 45 or price <= latest["BB_Low"] * 1.002) and latest["MACD_Hist"] > prev["MACD_Hist"]:
        direction = "🚀 TREND BUY (HIGH PROB)"
        color = "#2E7D32"
        sl = min(recent_floor - (atr * 0.3), price - (atr * 1.5))
        tp = price + (abs(price - sl) * 1.8)
        setup_note = "Macro uptrend aligned + pullback support + turning bullish momentum."

    elif not macro_bullish and price < latest["EMA_200"] and (rsi_now > 55 or price >= latest["BB_High"] * 0.998) and latest["MACD_Hist"] < prev["MACD_Hist"]:
        direction = "💥 TREND SELL (HIGH PROB)"
        color = "#C62828"
        sl = max(recent_ceiling + (atr * 0.3), price + (atr * 1.5))
        tp = price - (abs(sl - price) * 1.8)
        setup_note = "Macro downtrend aligned + pullback resistance + turning bearish momentum."

    # Tier B: Counter-Trend Bounce Warning (Prevents "Falling Knife" Traps)
    elif rsi_prev < 30 and rsi_now >= 30 and latest["MACD_Hist"] > prev["MACD_Hist"]:
        direction = "⚠️ SCALP BOUNCE BUY (COUNTER-TREND)"
        color = "#EF6C00"
        sl = recent_floor - (atr * 0.4)
        tp = price + (abs(price - sl) * 1.5)
