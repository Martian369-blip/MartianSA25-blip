import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go
import datetime
import os

# Custom layout and calculation safety fallbacks if internal modules are missing
class EngineFallback:
    @staticmethod
    def calculate_rsi(df, window=14):
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))

try:
    import engine as eng
except ImportError:
    eng = EngineFallback

try:
    import layout_config as lc
    has_layout_style = True
except ImportError:
    has_layout_style = False

try:
    import chart_render as cr
    has_chart_engine = True
except ImportError:
    has_chart_engine = False

# Initialize premium terminal view window layout
st.set_page_config(page_title="MARS_BOT V18.0 God Mode", page_icon="🛸", layout="wide")

if has_layout_style:
    try: lc.load_ig_style()
    except Exception: pass

PERSISTENT_FILE = "ledger_vault.csv"

def load_persistent_ledger():
    if os.path.exists(PERSISTENT_FILE):
        try:
            df = pd.read_csv(PERSISTENT_FILE)
            if not df.empty: return df
        except Exception: pass
    return pd.DataFrame(columns=["Timestamp", "Asset", "Action", "Price", "Matrix RSI", "Status"])

def save_persistent_ledger(df):
    df.to_csv(PERSISTENT_FILE, index=False)

# Robust Session Matrix Memory Initializations
if "journal_db" not in st.session_state: st.session_state["journal_db"] = load_persistent_ledger()
if "cached_target_asset" not in st.session_state: st.session_state["cached_target_asset"] = "USDZAR=X"
if "cached_display_name" not in st.session_state: st.session_state["cached_display_name"] = "USD/ZAR (US Dollar)"
if "price" not in st.session_state: st.session_state["price"] = 18.2540
if "direction" not in st.session_state: st.session_state["direction"] = "⏳ HOLD / STANDBY"
if "color" not in st.session_state: st.session_state["color"] = "#757575"
if "h1_rsi" not in st.session_state: st.session_state["h1_rsi"] = 50.0
if "stop_loss" not in st.session_state: st.session_state["stop_loss"] = 0.0
if "take_profit" not in st.session_state: st.session_state["take_profit"] = 0.0

st.sidebar.markdown("### 🛡️ Capital Defense Deck")
account_balance_zar = st.sidebar.number_input("Wallet Capital Base (ZAR)", min_value=10.0, value=500.00, step=50.0)
max_risk_allowed_pct = st.sidebar.slider("Maximum Trade Allocation Risk (%)", 1.0, 10.0, 5.0)

# Master 60+ Unified Asset Catalog Mapping Node
ig_name_map = {
    "USDZAR=X": "USD/ZAR (US Dollar)",
    "EURZAR=X": "EUR/ZAR (Euro)",
    "GBPZAR=X": "GBP/ZAR (British Pound)",
    "AUDZAR=X": "AUD/ZAR (Aussie Dollar)",
    "JPYZAR=X": "JPY/ZAR (Japanese Yen)",
    "CADZAR=X": "CAD/ZAR (Canadian Dollar)",
    "CHFZAR=X": "CHF/ZAR (Swiss Franc)",
    "NZDZAR=X": "NZD/ZAR (Kiwi Dollar)",
    "GBPUSD=X": "GBP/USD (Cable)",
    "EURUSD=X": "EUR/USD (Fiber)",
    "USDJPY=X": "USD/JPY (Ninja)",
    "AUDUSD=X": "AUD/USD (Aussie)",
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
    "CC=F":     "Cocoa Futures",
    "KC=F":     "Coffee Futures",
    "SOL.JO":   "Sasol Ltd (JSE:SOL)",
    "FSR.JO":   "FirstRand Ltd (JSE:FSR)",
    "SBK.JO":   "Standard Bank Group (JSE:SBK)",
    "ANG.JO":   "Anglogold Ashanti (JSE:ANG)",
    "IMP.JO":   "Impala Platinum (JSE:IMP)",
    "NPN.JO":   "Naspers Ltd (JSE:NPN)",
    "PRX.JO":   "Prosus NV (JSE:PRX)",
    "BTI.JO":   "British American Tobacco (JSE:BTI)",
    "AGL.JO":   "Anglo American plc (JSE:AGL)",
    "GFI.JO":   "Gold Fields Ltd (JSE:GFI)",
    "SLM.JO":   "Sanlam Ltd (JSE:SLM)",
    "ABG.JO":   "Absa Group Ltd (JSE:ABG)",
    "NED.JO":   "Nedbank Group (JSE:NED)",
    "MTN.JO":   "MTN Group Ltd (JSE:MTN)",
    "VOD.JO":   "Vodacom Group (JSE:VOD)",
    "AAPL":     "Apple Inc. (NASDAQ)",
    "NVDA":     "NVIDIA Corporation (NASDAQ)",
    "TSLA":     "Tesla Motors Inc. (NASDAQ)",
    "MSFT":     "Microsoft Corp. (NASDAQ)",
    "AMZN":     "Amazon.com Inc. (NASDAQ)",
    "META":     "Meta Platforms (NASDAQ)",
    "GOOGL":    "Alphabet Inc. (NASDAQ)",
    "AMD":      "Advanced Micro Devices (NASDAQ)",
    "NFLX":     "Netflix Inc. (NASDAQ)",
    "BTC-USD":  "Bitcoin / US Dollar",
    "ETH-USD":  "Ethereum / US Dollar",
    "SOL-USD":  "Solana / US Dollar",
    "BNB-USD":  "Binance Coin / US Dollar",
    "XRP-USD":  "Ripple / US Dollar",
    "^GSPC":    "S&P 500 Index (US Market)",
    "^NDX":     "NASDAQ 100 (US Tech)",
    "^DJI":     "Dow Jones Industrial 30",
    "^FTSE":    "FTSE 100 Index (London)",
    "^GDAXI":   "DAX Performance Index (Germany)",
    "^N225":    "Nikkei 225 Index (Japan)",
    "^J203.JO": "JSE All Share Index (South Africa)"
}

display_options = list(ig_name_map.values())

col_search, col_trigger = st.columns([0.75, 0.25])
with col_search:
    try: current_index = display_options.index(st.session_state["cached_display_name"])
    except ValueError: current_index = 0
    chosen_display = st.selectbox("🔍 MARKET VECTOR SELECTOR:", options=display_options, index=current_index, label_visibility="collapsed")

reverse_map = {v: k for k, v in ig_name_map.items()}
selected_ticker = reverse_map.get(chosen_display, "USDZAR=X")

with col_trigger:
    search_activated = st.button("🛰️ QUANT SCAN")

# ==================== ADVANCED CONFLUENCE ANALYTICS ENGINE ====================
def deep_technical_analysis(df_d, df_h):
    df_h = df_h.copy()
    close_series = pd.Series(df_h['Close'].values.flatten())
    
    d_close = pd.Series(df_d['Close'].values.flatten())
    daily_ema_50 = ta.trend.EMAIndicator(close=d_close, window=50).ema_indicator().fillna(d_close).iloc[-1]
    macro_trend_bullish = float(d_close.iloc[-1]) > float(daily_ema_50)

    df_h['RSI'] = ta.momentum.RSIIndicator(close=close_series, window=14).rsi().fillna(50.0).values
    df_h['EMA_200'] = ta.trend.EMAIndicator(close=close_series, window=200).ema_indicator().fillna(close_series).values
    df_h['ATR'] = ta.volatility.AverageTrueRange(high=df_h['High'], low=df_h['Low'], close=df_h['Close'], window=14).average_true_range().fillna(close_series * 0.002).values
    
    macd_obj = ta.trend.MACD(close=close_series)
    df_h['MACD_Hist'] = macd_obj.macd_diff().fillna(0.0).values
    
    bb_obj = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df_h['BB_High'] = bb_obj.bollinger_hband().values
    df_h['BB_Low'] = bb_obj.bollinger_lband().values

    recent_floor = float(df_h['Low'].tail(48).min())
    recent_ceiling = float(df_h['High'].tail(48).max())
    
    latest = df_h.iloc[-1]
    price = float(latest['Close'])
    atr = float(latest['ATR'])
    
    direction, color = "⏳ HOLD / STANDBY", "#757575"
    sl, tp = 0.0, 0.0
    
    if macro_trend_bullish and (price < latest['BB_Low'] * 1.01 or latest['RSI'] < 40) and latest['MACD_Hist'] > 0 and price > latest['EMA_200']:
        direction, color = "🚀 CONVERGENT BUY", "#4CAF50"
        sl = recent_floor - (atr * 0.5)
        tp = price + (abs(price - sl) * 2.0)
        
    elif not macro_trend_bullish and (price > latest['BB_High'] * 0.99 or latest['RSI'] > 60) and latest['MACD_Hist'] < 0 and price < latest['EMA_200']:
        direction, color = "💥 CONVERGENT SELL", "#E53935"
        sl = recent_ceiling + (atr * 0.5)
        tp = price - (abs(sl - price) * 2.0)
        
    return direction, color, price, float(latest['RSI']), sl, tp, df_h

if search_activated or st.session_state["cached_target_asset"] != selected_ticker:
    st.session_state["cached_target_asset"] = selected_ticker
    st.session_state["cached_display_name"] = chosen_display
    try:
        with st.spinner("Executing Full Technical Alignment Sweep..."):
            df_d = yf.Ticker(selected_ticker).history(period="6mo", interval="1d")
            df_h = yf.Ticker(selected_ticker).history(period="1mo", interval="1h")
            
            if not df_d.empty and not df_h.empty:
                direction, color, price, rsi, sl, tp, df_analyzed = deep_technical_analysis(df_d, df_h)
                st.session_state["direction"] = direction
                st.session_state["color"] = color
                st.session_state["price"] = price
                st.session_state["h1_rsi"] = rsi
                st.session_state["stop_loss"] = sl
                st.session_state["take_profit"] = tp
    except Exception as e:
        st.sidebar.error(f"Matrix Engine Sync Warning: {str(e)}")

# ==================== INTERFACE LAYER ====================
st.sidebar.markdown("<h3 style='color:#4CAF50 !important; font-weight:900;'>☰ MAIN CORE</h3>", unsafe_allow_html=True)
navigation_sheets = ["📊  TERMINAL SIGNALS", "📡  SATELLITE NEWS", "🕹️  LEDGER JOURNAL"]
page_select = st.sidebar.radio("CHOOSE MODULE SHEET:", options=navigation_sheets)

if page_select == "📊  TERMINAL SIGNALS":
    st.markdown(f"#### 📡 Telemetry Feed Workspace: <span style='color:#4CAF50;'>{st.session_state['cached_display_name']}</span>", unsafe_allow_html=True)
    
    is_zar = "ZAR" in st.session_state['cached_target_asset'] or ".JO" in st.session_state['cached_target_asset']
    c_prefix = "R " if is_zar else "$ "
    
    spot_str = f"{c_prefix}{st.session_state['price']:.4f}"
    direction_str = str(st.session_state['direction'])
    color_str = str(st.session_state['color'])
    h1_rsi_str = f"{st.session_state['h1_rsi']:.1f}"
    
