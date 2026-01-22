import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. 주급 데이터 가져오기
def get_payout_data(conn): 
    try:
        df = conn.read(worksheet="payouts", ttl="30m") 
        if df is not None and not df.empty:
            df['payout_amount'] = pd.to_numeric(
                df['payout_amount'].astype(str).str.replace(',', ''), errors='coerce'
            ).fillna(0)
            df['category'] = df['category'].fillna('미분류')
            df['handle'] = df['handle'].astype(str).str.strip()
            if 'name' not in df.columns: df['name'] = df['handle']
            else: df['name'] = df['name'].fillna(df['handle'])
            if 'bio' not in df.columns: df['bio'] = ""
            else: df['bio'] = df['bio'].fillna("")
        return df
    except Exception as e:
        return pd.DataFrame(columns=['handle', 'name', 'payout_amount', 'category', 'bio'])

# 2. 주급 맵 렌더링 (인자 개수 축소: conn, follower_df 2개만 받음)
def render_payout_page(conn, follower_df):
    st.title("💰 트위터 주급 맵 (Weekly Payout)")
    st.caption("이번 주 트위터 수익 정산 현황")

    payout_df = get_payout_data(conn)
    
    if not payout_df.empty:
        # 0원 제외
        display_df = payout_df[payout_df['payout_amount'] > 0]
        
        # ---------------------------------------------------------
        # [NEW] 카테고리 선택 & 통합 보기 버튼을 메인 화면에 배치
        # ---------------------------------------------------------
        # 카테고리 목록 생성
        all_cats = ["전체보기"] + sorted(display_df['category'].unique().tolist())
        
        # 화면 분할 (왼쪽: 카테고리 버튼 / 오른쪽: 통합 토글)
        col_cat, col_opt = st.columns([0.75, 0.25])
        
        with col_cat:
            # 가로형 라디오 버튼 (메인 화면 배치)
            selected_category = st.radio(
                "카테고리 선택", 
                all_cats, 
                horizontal=True, 
                label_visibility="collapsed",
                key="payout_category_main"
            )
            
        with col_opt:
            # 전체보기일 때만 토글 표시
            merge_categories = False
            if selected_category == "전체보기":
                merge_categories = st.toggle("통합 보기", value=False, key="payout_merge_toggle")

        st.divider() # 구분선 추가

        # ---------------------------------------------------------
        # 데이터 필터링
        # ---------------------------------------------------------
        if selected_category != "전체보기":
            display_df = display_df[display_df['category'] == selected_category]
        
        if display_df.empty:
            st.info(f"'{selected_category}' 데이터가 없습니다.")
            return

        # 팔로워 데이터 병합
        if not follower_df.empty:
            merged_df = pd.merge(
                display_df, 
                follower_df[['handle', 'followers']], 
                on='handle', 
                how='left'
            )
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
        # 트리맵 차트
        # ---------------------------------------------------------
        display_df['chart_label'] = display_df.apply(
            lambda x: f"{str(x['name'])}<br><span style='font-size:0.7em; font-weight:normal;'>@{str(x['handle'])}</span>", 
            axis=1
        )
        
        if merge_categories:
            display_df['root_group'] = "전체 (All)"
            path_list = ['root_group', 'chart_label']
        else:
            path_list = ['category', 'chart_label']

        fig = px.treemap(
            display_df, 
            path=path_list, 
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
        # 리더보드 리스트
        # ---------------------------------------------------------
        col_head, col_toggle = st.columns([1, 0.3])
        with col_head:
            st.subheader("📋 주급 랭킹 (Payout Ranking)")
        with col_toggle:
            expand_view = st.toggle("전체 펼치기", value=False, key="payout_ranking_toggle")

        ranking_df = display_df.sort_values(by='payout_amount', ascending=False).reset_index(drop=True)
        
        list_html = ""
        for index, row in ranking_df.iterrows():
            rank = index + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
            img_url = f"https://unavatar.io/twitter/{row['handle']}"
            
            bio_content = row['bio'] if row['bio'] else "수익 인증 상세 정보가 없습니다."
            follower_count = int(row['followers']) if 'followers' in row else 0
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
                        <div class="rank-extra"></div>
                        <div class="rank-stats-group" style="width: 200px;">
                            <div class="rank-category" style="background-color: #1F2937; color: #9CA3AF;">👥 {follower_text}</div>
                            <div class="rank-followers" style="width: 80px; color: #10B981;">${int(row['payout_amount']):,}</div>
                        </div>
                    </div>
                </summary>
                <div class="bio-box">
                    <div class="bio-header">💰 PAYOUT INFO</div>
                    <div class="bio-content">{bio_content}</div>
                    <a href="https://twitter.com/{row['handle']}" target="_blank" class="bio-link-btn">Visit Profile ↗</a>
                </div>
            </details>
            """

        with st.container(height=600 if not expand_view else None):
            st.markdown(list_html, unsafe_allow_html=True)

    else:
        st.info("주급 데이터를 불러올 수 없습니다. 'payouts' 시트를 확인해주세요.")
