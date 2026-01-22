import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. 주급 데이터 가져오기 (캐싱 에러 방지를 위해 ttl 사용)
def get_payout_data(conn): 
    try:
        # 30분 캐시
        df = conn.read(worksheet="payouts", ttl="30m") 
        
        if df is not None and not df.empty:
            # 숫자 변환 (콤마 제거)
            df['payout_amount'] = pd.to_numeric(
                df['payout_amount'].astype(str).str.replace(',', ''), errors='coerce'
            ).fillna(0)
            
            df['category'] = df['category'].fillna('미분류')
            df['handle'] = df['handle'].astype(str)
            
            # 이름 없으면 핸들로 대체
            if 'name' not in df.columns: df['name'] = df['handle']
            else: df['name'] = df['name'].fillna(df['handle'])
            
            # 트위터 맵과 동일한 구조를 위해 bio 컬럼이 없으면 빈칸 처리
            if 'bio' not in df.columns: df['bio'] = ""
            else: df['bio'] = df['bio'].fillna("")
            
        return df
    except Exception as e:
        return pd.DataFrame(columns=['handle', 'name', 'payout_amount', 'category', 'bio'])

# 2. 주급 맵 렌더링
def render_payout_page(conn):
    st.title("💰 트위터 주급 맵 (Weekly Payout)")
    st.caption("이번 주 트위터 수익 정산 현황")

    df = get_payout_data(conn)
    
    if not df.empty:
        # 0원인 사람은 제외
        display_df = df[df['payout_amount'] > 0]
        
        if display_df.empty:
            st.info("주급 데이터가 없습니다.")
            return

        # 상단 요약 카드
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

        # ---------------------------------------------------------
        # 1. 트리맵 차트 (스타일 팔로워 맵과 통일)
        # ---------------------------------------------------------
        display_df['chart_label'] = display_df.apply(
            lambda x: f"{str(x['name'])}<br><span style='font-size:0.7em; font-weight:normal;'>@{str(x['handle'])}</span>", 
            axis=1
        )
        
        # 돈이니까 초록색 테마 사용
        fig = px.treemap(
            display_df, 
            path=['category', 'chart_label'], 
            values='payout_amount', 
            color='payout_amount',
            custom_data=['name', 'handle'],
            color_continuous_scale=[
                (0.0, '#1B2E1E'), (0.2, '#2E5936'), (0.5, '#34A853'), (1.0, '#A8D67F')
            ],
            template="plotly_dark"
        )
        
        fig.update_traces(
            texttemplate='<b>%{customdata[0]}</b><br><b style="font-size:1.2em">$%{value:,.0f}</b><br><span style="font-size:0.8em; color:#D1D5DB">%{percentRoot:.1%}</span>',
            textfont=dict(size=20, family="sans-serif", color="white"),
            textposition="middle center",
            marker=dict(line=dict(width=3, color='#000000')),
            root_color="#000000",
            hovertemplate='<b>%{customdata[0]}</b> (@%{customdata[1]})<br>Payout: $%{value:,.0f}<br>Share: %{percentRoot:.1%}<extra></extra>'
        )
        
        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0), 
            paper_bgcolor='#000000', plot_bgcolor='#000000', 
            height=600, coloraxis_showscale=False,
            hoverlabel=dict(bgcolor="#1C1F26", bordercolor="#10B981", font=dict(size=18, color="white"), namelength=-1)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.write("")

        # ---------------------------------------------------------
        # 2. 리더보드 리스트 (팔로워 맵과 동일한 HTML 구조 적용)
        # ---------------------------------------------------------
        col_head, col_toggle = st.columns([1, 0.3])
        with col_head:
            st.subheader("📋 주급 랭킹 (Payout Ranking)")
        with col_toggle:
            expand_view = st.toggle("전체 펼치기", value=False, key="payout_toggle")

        # 주급 순으로 정렬
        ranking_df = display_df.sort_values(by='payout_amount', ascending=False).reset_index(drop=True)
        view_total = ranking_df['payout_amount'].sum()
        
        list_html = ""
        for index, row in ranking_df.iterrows():
            rank = index + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
            img_url = f"https://unavatar.io/twitter/{row['handle']}"
            share_pct = (row['payout_amount'] / view_total * 100) if view_total > 0 else 0
            
            # 주급 맵에는 'bio'가 없을 수도 있으므로 처리
            bio_content = row['bio'] if row['bio'] else "수익 인증 상세 정보가 없습니다."

            list_html += f"""
            <details {'open' if expand_view else ''}>
                <summary>
                    <div class="ranking-row">
                        <div class="rank-col-1">
                            <div class="rank-num">{medal}</div>
                            <img src="{img_url}" class="rank-img" onerror="this.style.display='none'">
                        </div>
                        <div class="rank-info">
                            <div class="rank-name">{row['name']}</div>
                            <div class="rank-handle">@{row['handle']}</div>
                        </div>
                        <div class="rank-extra">
                            </div>
                        <div class="rank-stats-group">
                            <div class="rank-category">{row['category']}</div>
                            <div class="rank-share">{share_pct:.1f}%</div>
                            <div class="rank-followers">${int(row['payout_amount']):,}</div>
                        </div>
                    </div>
                </summary>
                <div class="bio-box">
                    <div class="bio-header">💰 PAYOUT INFO</div>
                    <div class="bio-content">{bio_content}</div>
                    <a href="https://twitter.com/{row['handle']}" target="_blank" class="bio-link-btn">
                        Visit Profile ↗
                    </a>
                </div>
            </details>
            """

        with st.container(height=600 if not expand_view else None):
            st.markdown(list_html, unsafe_allow_html=True)

    else:
        st.info("주급 데이터를 불러올 수 없습니다. 'payouts' 시트를 확인해주세요.")
