import plotly.graph_objects as go

def draw_advanced_chart(df, title_name):
    """Generates an interactive, zoomable candlestick chart layout with structural filters."""
    # Slice recent candles for high-definition presentation
    plot_df = df.tail(100)
    
    fig = go.Figure()
    
    # 🕯️ Draw Base Candlesticks
    fig.add_trace(go.Candlestick(
        x=plot_df.index, open=plot_df['Open'], high=plot_df['High'],
        low=plot_df['Low'], close=plot_df['Close'], name="Candles"
    ))
    
    # 💎 Overlay Trend Baseline (200 EMA)
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['EMA_200'],
        line=dict(color='#ff9900', width=1.5), name="200 EMA"
    ))
    
    # 🚀 Plot Signal Triggers onto the Candles
    buys = plot_df[plot_df['Signal'] == "BUY"]
    sells = plot_df[plot_df['Signal'] == "SELL"]
    
    fig.add_trace(go.Scatter(
        x=buys.index, y=buys['Low'] * 0.998, mode='markers',
        marker=dict(symbol='triangle-up', size=12, color='#2ecc71'), name="BUY Signal"
    ))
    
    fig.add_trace(go.Scatter(
        x=sells.index, y=sells['High'] * 1.002, mode='markers',
        marker=dict(symbol='triangle-down', size=12, color='#e74c3c'), name="SELL Signal"
    ))
    
    fig.update_layout(
        title=f"📊 {title_name} High-Res Structural Chart",
        xaxis_rangeslider_visible=False, height=450,
        template="plotly_dark", background_color="#12141c"
    )
    return fig
