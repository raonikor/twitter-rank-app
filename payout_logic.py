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
            df['handle'] = df['handle'].astype(str).str.strip() # 공백 제거
            
            # 이름 없으면 핸들로 대체
            if 'name' not in df.columns: df['name'] = df['handle']
            else: df['name'] = df['name'].fillna(df['handle'])
            
            # bio 컬럼 처리
            if 'bio' not in df.columns: df['bio'] = ""
            else: df['bio'] = df['bio'].fillna("")
            
        return df
    except Exception as e:
        return pd.DataFrame(columns=['handle', 'name', 'payout_amount', 'category', 'bio'])

# 2. 주급 맵 렌더링 (follower_df 인자 추가됨)
def render_payout_page(conn, follower_df):
    st.title("💰 트위터 주급 맵 (Weekly Payout)")
    st.caption("이번 주 트위터 수익 정산 현황")

    payout_df = get_payout_data(conn)
    
    if not payout_df.empty:
        # 0원인 사람은 제외
        display_df = payout_df[payout_df['payout_amount'] > 0]
        
        if display_df.empty:
            st.info("주급 데이터가 없습니다.")
            return

        # ---------------------------------------------------------
        # [핵심] 팔로워 데이터와 병합 (Merge)
        # ---------------------------------------------------------
        if not follower_df.empty:
            # 핸들 기준으로 팔로워 정보만 가져와서 합치기
            # follower_df에서 handle과 followers 컬럼만 사용
            merged_df = pd.merge(
                display_df, 
                follower_df[['handle', 'followers']], 
                on='handle', 
                how='left'
            )
            # 매칭 안 된 경우(팔로워 맵에 없는 사람) 0으로 처리
            merged_df['followers'] = merged_df['followers'].fillna(0)
            display_df = merged_df

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
        # 1. 트리맵 차트
        # ---------------------------------------------------------
        display_df['chart_label'] = display_df.apply(
            lambda x: f"{str(x['name'])}<br><span style='font-size:0.7em; font-weight:normal;'>@{str(x['handle'])}</span>", 
            axis=1
        )
        
        # 팔로워 맵과 동일한 그라데이션 적용
        fig = px.treemap(
            display_df, 
            path=['category', 'chart_label'], 
            values='payout_amount', 
            color='payout_amount', 
            custom_data=['name', 'handle'],
            color_continuous_scale=[(0.00, '#2E2B4E'), (0.05, '#353263'), (0.10, '#3F3C5C'), (0.15, '#464282'), (0.20, '#4A477A'), (0.25, '#4A5D91'), (0.30, '#4A6FA5'), (0.35, '#537CA8'), (0.40, '#5C8BAE'), (0.45, '#5C98AE'), (0.50, '#5E9CA8'), (0.55, '#5E9E94'), (0.60, '#5F9E7F'), (0.65, '#729E6F'), (0.70, '#859E5F'), (0.75, '#969E5F'), (0.80, '#A89E5F'), (0.85, '#AD905D'), (0.90, '#AE815C'), (0.95, '#AE6E5C'), (1.00, '#AE5C5C')],
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
        # 2. 리더보드 리스트
        # ---------------------------------------------------------
        col_head, col_toggle = st.columns([1, 0.3])
        with col_head:
            st.subheader("📋 주급 랭킹 (Payout Ranking)")
        with col_toggle:
            expand_view = st.toggle("전체 펼치기", value=False, key="payout_toggle")

        # 주급 순으로 정렬
        ranking_df = display_df.sort_values(by='payout_amount', ascending=False).reset_index(drop=True)
        
        list_html = ""
        for index, row in ranking_df.iterrows():
            rank = index + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
            img_url = f"https://unavatar.io/twitter/{row['handle']}"
            
            # 바이오 정보 (없으면 기본 문구)
            bio_content = row['bio'] if row['bio'] else "수익 인증 상세 정보가 없습니다."
            
            # [NEW] 팔로워 수 표시 (데이터가 병합되었으므로 row['followers'] 사용 가능)
            # 만약 팔로워 데이터가 없으면 0으로 나옴
            follower_count = int(row['followers']) if 'followers' in row else 0
            
            # 팔로워 숫자를 K, M 단위로 변환하는 간단한 로직 (선택사항)
            # 여기서는 그냥 콤마 포맷 사용
            follower_text = f"{follower_count:,}"

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
                        <div class="rank-stats-group" style="width: 200px;"> <div class="rank-category" style="background-color: #1F2937; color: #9CA3AF;">👥 {follower_text}</div>
                            <div class="rank-followers" style="width: 80px; color: #10B981;">${int(row['payout_amount']):,}</div>
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
