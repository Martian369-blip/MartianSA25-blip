import streamlit as st

def apply_martian_theme():
    """Injects dark theme visual enhancements and layout optimizations."""
    st.markdown("""
        <style>
        .metric-card {
            background-color: #1e222b;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #2f3440;
            margin-bottom: 10px;
        }
        .signal-buy { color: #2ecc71; font-weight: bold; }
        .signal-sell { color: #e74c3c; font-weight: bold; }
        .signal-hold { color: #f1c40f; font-weight: bold; }
        </style>
    """, unsafe_style_allowed=True)

def render_small_account_header(balance, risk_pct):
    """Renders a responsive dashboard controller for capital defense metrics."""
    st.sidebar.markdown("### 🛡️ Account Settings")
    st.sidebar.markdown(f"**Capital Profile:** Small Account Optimization Mode")
    
    # Return values for dynamic configuration binding
    ret_balance = st.sidebar.number_input("Wallet Capital Base (ZAR)", min_value=10.0, value=float(balance), step=50.0)
    ret_risk = st.sidebar.slider("Maximum Trade Allocation Risk (%)", 1.0, 10.0, float(risk_pct))
    return ret_balance, ret_risk
