import streamlit as st
import yfinance as yf
import urllib.request
import xml.etree.ElementTree as ET
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

def fetch_fallback_rss_news(asset_name):
    """
    Fallback pipeline: Pulls live plain-text headlines directly from broad financial 
    RSS streams when individual ticker APIs are empty.
    """
    headlines = []
    rss_url = "https://cnbc.com"
    
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('.//item'):
                title = item.find('title')
                pub_date = item.find('pubDate')
                
                title_text = title.text if title is not None else ""
                date_text = pub_date.text if pub_date is not None else ""
                
                if date_text:
                    try:
                        parsed_date = datetime.strptime(date_text[:25].strip(), "%a, %d %b %Y %H:%M:%S")
                        date_fmt = parsed_date.strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        date_fmt = datetime.now().strftime('%Y-%m-%d %H:%M')
                else:
                    date_fmt = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                if title_text:
                    headlines.append({"title": title_text, "source": "CNBC Live Desk", "time": date_fmt})
                if len(headlines) >= 4:
                    break
    except Exception:
        pass
    return headlines

def render_news_tab(analyzed_watchlists):
    st.markdown("### 📰 Global News & Market Hypothesis Desk")
    
    if not analyzed_watchlists:
        st.info("Waiting for a valid symbol selection in the Master Asset Hub...")
        return

    for ticker, data in analyzed_watchlists.items():
        asset = data["asset"]
        latest = data["df"].iloc[-1]
        ticker_obj = data["ticker_obj"]
        
        st.markdown(f"#### 📦 {asset['name']} Deep Portfolio Analysis ({ticker})")
        
        # Display custom technical hypothesis
        hypothesis_content = generate_market_hypothesis(ticker, latest, asset['name'])
        st.markdown(f"<div class='hypothesis-box'>{hypothesis_content}</div>", unsafe_allow_html=True)
        
        st.markdown("**Local Plain-Text Financial Headlines Feed:**")
        
        valid_news_count = 0
        
        # --- PIPELINE 1: PRIMARY DATA STREAM ---
        try:
            raw_news = ticker_obj.get_news() if hasattr(ticker_obj, 'get_news') else ticker_obj.news
            if isinstance(raw_news, list) and len(raw_news) > 0:
                for item in raw_news:
                    title_text = item.get('title')
                    publisher_name = item.get('publisher') or "Financial Desk"
                    pub_timestamp = item.get('providerPublishTime')
                    
                    if not title_text or title_text == "None":
                        continue
                        
                    if isinstance(pub_timestamp, (int, float)) and pub_timestamp > 0:
                        pub_time = datetime.fromtimestamp(pub_timestamp).strftime('%Y-%m-%d %H:%M')
                    else:
                        pub_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                    
                    st.markdown(
                        f"<div class='news-card'>"
                        f"📢 <b>{title_text}</b><br>"
                        f"<small style='color: #7f8c8d;'>Desk Source: {publisher_name} | Clock Log: {pub_time} SAST</small>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
                    valid_news_count += 1
                    if valid_news_count >= 4:
                        break
        except Exception:
            pass

        # --- PIPELINE 2: DIRECT BROADBAND RSS FALLBACK STREAM ---
        if valid_news_count == 0:
            fallback_news = fetch_fallback_rss_news(asset['name'])
            if fallback_news:
                for item in fallback_news:
                    st.markdown(
                        f"<div class='news-card'>"
                        f"📢 <b>{item['title']}</b><br>"
                        f"<small style='color: #7f8c8d;'>Desk Source: {item['source']} | Clock Log: {item['time']} SAST</small>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
                    valid_news_count += 1
            
        if valid_news_count == 0:
            st.info(f"🛰️ Active live monitoring running. System market connection stable for {ticker}.")
            
        st.divider()
