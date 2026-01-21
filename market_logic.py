# market_logic.py
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 1. 데이터 가져오는 함수 (캐시 포함)
@st.cache_data(ttl="5m") 
def get_market_data():
    tickers = {'KOSPI': '^KS11', 'Gold': 'GC=F', 'Ethereum': 'ETH-USD'}
    market_df = []
    for name, ticker in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="7d")
            hist = hist.dropna(subset=['Close'])
            if len(hist) >= 2: 
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0
                market_df.append({'Name': name, 'Price': current_price, 'Change': change_pct, 'Category': 'Major Asset'})
        except: continue
    return pd.DataFrame(market_df)

# 2. 화면에 그리는 함수 (Main 함수)
def render_market_page():
    st.title("📊 시장 지수 (Market Indices)")
    st.caption("Real-time Data: KOSPI, Gold, Ethereum")
    
    market_df = get_market_data()
    
    if not market_df.empty:
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        for i, row in market_df.iterrows():
            if i < 3:
                name, price, change = row['Name'], row['Price'], row['Change']
                color_class = "delta-up" if change >= 0 else "delta-down"
                arrow = "▲" if change >= 0 else "▼"
                with cols[i]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{name}</div>
                        <div class="metric-value">{price:,.2f}</div>
                        <div class="metric-delta {color_class}">{arrow} {change:.2f}%</div>
                    </div>""", unsafe_allow_html=True)
        
        st.write("")
        fig = px.treemap(
            market_df, path=['Category', 'Name'], values='Price', color='Change', 
            custom_data=['Change'], color_continuous_scale=['#EF4444', '#1F2937', '#10B981'], 
            color_continuous_midpoint=0, template="plotly_dark"
        )
        fig.update_traces(
            texttemplate='<b>%{label}</b><br>%{value:,.2f}<br>%{customdata[0]:.2f}%',
            textfont=dict(size=24, family="sans-serif", color="white"),
            textposition="middle center", marker=dict(line=dict(width=3, color='#000000')), root_color="#000000"
        )
        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='#000000', plot_bgcolor='#000000', height=500,
            font=dict(family="sans-serif"), coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else: st.error("데이터 로딩 중...")
