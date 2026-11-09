import streamlit as st
import yfinance as yf
from datetime import datetime

def generate_market_hypothesis(ticker, latest, asset_name):
    price = latest['Close']
    ema = latest['EMA_200']
    rsi = latest['RSI']
    
    if price > ema:
        bias = "BULLISH ACCUMULATION"
        action = f"Look for buy setups above R{ema:.2f} if trading a ZAR pair." if "ZAR" in ticker else f"Look for dynamic support retests above ${ema:.2f}."
    else:
        bias = "BEARISH DISTRIBUTION"
        action = f"Expect heavy overhead structural resistance around the R{ema:.2f} area." if "ZAR" in ticker else f"Expect ceiling selling pressure near ${ema:.2f}."

    return (
        f"🧭 **Macro Bias:** {bias} | **Current Momentum (RSI):** {rsi:.1f}\n\n"
        f"📊 **Market Hypothesis:** {asset_name} ({ticker}) is trading relative to its 200 hourly EMA line. "
        f"With the technical oscillator sitting at {rsi:.1f}, conditions point to clear macro-trend positioning. {action}"
    )

def render_news_tab(analyzed_watchlists):
    st.markdown("### 📰 Global News & Market Hypothesis Desk")
    
    if not analyzed_watchlists:
        st.info("Waiting for a valid symbol to be entered in the Master Search Engine...")
        return

    for ticker, data in analyzed_watchlists.items():
        asset = data["asset"]
        latest = data["df"].iloc[-1]
        ticker_obj = data["ticker_obj"]
        
        st.markdown(f"#### 📦 {asset['name']} Deep Portfolio Analysis ({ticker})")
        
        # Display the custom dynamic technical hypothesis
        hypothesis_content = generate_market_hypothesis(ticker, latest, asset['name'])
        st.markdown(f"<div class='hypothesis-box'>{hypothesis_content}</div>", unsafe_allow_html=True)
        
        st.markdown("**Local Plain-Text Financial Headlines Feed:**")
        try:
            news_items = ticker_obj.news
            if news_items:
                for item in news_items[:4]:  # Expanded to a clean top 4 plain-text summary list
                    pub_time = datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M')
                    title_text = item.get('title')
                    publisher_name = item.get('publisher')
                    
                    st.markdown(
                        f"<div class='news-card'>"
                        f"📢 <b>{title_text}</b><br>"
                        f"<small style='color: #7f8c8d;'>Desk Source: {publisher_name} | Timestamp: {pub_time} SAST</small>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
            else:
                st.info(f"No active news stream found for {ticker}. Displaying systemic technical monitoring charts only.")
        except Exception:
            st.info("Headline feed stream initializing. Live market monitoring active.")
        st.divider()
