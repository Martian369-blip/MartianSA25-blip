import streamlit as st
import plotly.graph_objects as go

def apply_martian_theme():
    """Injects high-contrast dark room aesthetics into the workspace."""
    st.markdown("""
        <style>
        .metric-card {
            background-color: #121620;
            padding: 18px;
            border-radius: 12px;
            border: 1px solid #232936;
            margin-bottom: 12px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #121620;
            border: 1px solid #232936;
            border-radius: 6px 6px 0px 0px;
            padding: 10px 20px;
        }
        </style>
    """, unsafe_allow_html=True)

def render_small_account_header(balance=500.00, risk_pct=5.0):
    """Compiles capital parameters inside the lateral navigation frame."""
    st.sidebar.markdown("### 🛡️ Capital Defense Deck")
    st.sidebar.caption("Sizing calibrated for ZAR Micro Accounts")
    
    ret_balance = st.sidebar.number_input("Wallet Capital Base (ZAR)", min_value=10.0, value=float(balance), step=50.0)
    ret_risk = st.sidebar.slider("Maximum Trade Allocation Risk (%)", 1.0, 10.0, float(risk_pct))
    return ret_balance, ret_risk

def draw_advanced_chart(df, title_name):
    """Generates an interactive, zoomable candlestick chart layout."""
    plot_df = df.tail(100)
    fig = go.Figure()
    
    # 🕯️ Render Primary Candlestick Series
    fig.add_trace(go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'], name="Price Matrix"
    ))
    
    # 🟠 Overlay Trend Line (200 EMA)
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['EMA_200'],
        line=dict(color='#ff9900', width=1.5), name="200 EMA Engine"
    ))
    
    # 🚀 Mark Algorithmic Signals Natively onto the chart
    buys = plot_df[plot_df['Signal'] == "BUY"]
    sells = plot_df[plot_df['Signal'] == "SELL"]
    
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys['Low'] * 0.998, mode='markers',
        marker=dict(symbol='triangle-up', size=12, color='#2ecc71'), name="BUY Event"
    ))
    
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells['High'] * 1.002, mode='markers',
        marker=dict(symbol='triangle-down', size=12, color='#e74c3c'), name="SELL Event"
    ))
    
    fig.update_layout(
        title=f"📊 {title_name} Telemetry Grid Matrix",
        xaxis_rangeslider_visible=False, height=450,
        template="plotly_dark", paper_bgcolor="#0c0e14", plot_bgcolor="#0c0e14",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig
