# payout_logic.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# [수정] 인자 이름 앞에 언더바(_) 추가: _conn
# 이렇게 하면 Streamlit이 캐싱할 때 이 객체는 무시합니다.
@st.cache_data(ttl="30m")
def get_payout_data(_conn): 
    try:
        # 내부에서도 _conn으로 사용
        df = _conn.read(worksheet="payouts", ttl="0") 
        
        if df is not None and not df.empty:
            # 숫자 변환 (콤마 제거 등 안전장치)
            df['payout_amount'] = pd.to_numeric(
                df['payout_amount'].astype(str).str.replace(',', ''), errors='coerce'
            ).fillna(0)
            
            df['category'] = df['category'].fillna('미분류')
            df['handle'] = df['handle'].astype(str)
            if 'name' not in df.columns: df['name'] = df['handle']
            else: df['name'] = df['name'].fillna(df['handle'])
            
        return df
    except Exception as e:
        return pd.DataFrame(columns=['handle', 'name', 'payout_amount', 'category'])

# 2. 주급 맵 렌더링
def render_payout_page(conn):
    st.title("💰 트위터 주급 맵 (Weekly Payout)")
    st.caption("이번 주 트위터 수익 정산 현황")

    # 호출할 때는 그냥 conn을 넘겨주면 됩니다. (받는 쪽이 _conn으로 받음)
    df = get_payout_data(conn)
    
    if not df.empty:
        # 0원인 사람은 제외
        display_df = df[df['payout_amount'] > 0]
        
        if display_df.empty:
            st.info("주급 데이터가 없습니다.")
            return

        # 상단 요약
        total_payout = display_df['payout_amount'].sum()
        top_earner = display_df.loc[display_df['payout_amount'].idxmax()]
        
        col1, col2 = st.columns(2)
        with col1: 
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">총 지급액 (Total Payout)</div>
                <div class="metric-value">${total_payout:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with col2: 
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">주급 1위 (Top Earner)</div>
                <div class="metric-value">{top_earner['name']} (${top_earner['payout_amount']:,.0f})</div>
            </div>""", unsafe_allow_html=True)

        st.write("")

        # 트리맵 (돈이니까 초록색 테마)
        display_df['chart_label'] = display_df['name'] + "<br><span style='font-size:0.8em;'>@" + display_df['handle'] + "</span>"
        
        fig = px.treemap(
            display_df, 
            path=['category', 'chart_label'], 
            values='payout_amount', 
            color='payout_amount',
            custom_data=['name', 'handle'],
            # 초록색 그라데이션
            color_continuous_scale=[
                (0.0, '#1B2E1E'), (0.2, '#2E5936'), (0.5, '#34A853'), (1.0, '#A8D67F')
            ],
            template="plotly_dark"
        )
        
        fig.update_traces(
            texttemplate='<b>%{customdata[0]}</b><br>$%{value:,.0f}',
            textfont=dict(size=18, family="sans-serif", color="white"),
            hovertemplate='<b>%{customdata[0]}</b> (@%{customdata[1]})<br>Payout: $%{value:,.0f}<extra></extra>',
            marker=dict(line=dict(width=2, color='#000000')),
            root_color="#000000"
        )
        
        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0), 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=600, coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 리스트 (테이블)
        st.subheader("📋 주급 랭킹")
        st.dataframe(
            display_df[['name', 'handle', 'category', 'payout_amount']].sort_values('payout_amount', ascending=False),
            column_config={
                "name": "이름",
                "handle": "핸들",
                "category": "카테고리",
                "payout_amount": st.column_config.NumberColumn("주급 ($)", format="$%d")
            },
            hide_index=True,
            use_container_width=True
        )

    else:
        st.info("주급 데이터를 불러올 수 없습니다. 'payouts' 시트를 확인해주세요.")
