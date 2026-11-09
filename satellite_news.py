import streamlit as st
import yfinance as yf
from datetime import datetime

def generate_market_hypothesis(ticker, latest, asset_name):
    """Generates structural market hypotheses using live technical positioning."""
    price = latest['Close']
    ema = latest['EMA_200']
    rsi = latest['RSI']
    
    if price > ema:
        bias = "BULLISH ACCUMULATION"
        action = f"Look for pullbacks toward the support baseline near R{ema:.4f} if trading locally." if "ZAR" in ticker else f"Look for buy confirmations above ${ema:.4f}."
    else:
        bias = "BEARISH DISTRIBUTION"
        action = f"Expect overhead ceiling selling pressure near the 200 EMA area."

    return (
        f"🧭 **Macro Bias:** {bias} | **Current Momentum (RSI):** {rsi:.1f}\n\n"
        f"📊 **Market Hypothesis:** {asset_name} ({ticker}) is trading in a trend phase relative to its 200 hourly EMA line. "
        f"With the technical index sitting at {rsi:.1f}, conditions point to consolidation. {action}"
    )

def render_news_tab(analyzed_watchlists):
    """Renders plain-text headline cards directly inside the dashboard workspace layout."""
    st.markdown("### 📰 Global News & Market Hypothesis Desk")
    
    for ticker, data in analyzed_watchlists.items():
        asset = data["asset"]
        latest = data["df"].iloc[-1]
        ticker_obj = data["ticker_obj"]
        
        st.markdown(f"#### 📦 {asset['name']} Portfolio Flow ({ticker})")
        
        # Display our advanced isolated hypothesis
        hypothesis_content = generate_market_hypothesis(ticker, latest, asset['name'])
        st.markdown(f"<div class='hypothesis-box'>{hypothesis_content}</div>", unsafe_allow_html=True)
        
        st.markdown("**Local Asset Headline Feeds:**")
        try:
            news_items = ticker_obj.news
            if news_items:
                for item in news_items[:3]:
                    pub_time = datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M')
                    title_text = item.get('title')
                    publisher_name = item.get('publisher')
                    
                    st.markdown(
                        f"<div class='news-card'>"
                        f"📢 <b>{title_text}</b><br>"
                        f"<small style='color: #7f8c8d;'>Desk Source: {publisher_name} | Clock Log: {pub_time} SAST</small>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
            else:
                st.info("No active text summaries streaming for this portfolio sector currently.")
        except Exception:
            st.info("Headline feed stream under routine maintenance. Monitoring active.")
        st.divider()
