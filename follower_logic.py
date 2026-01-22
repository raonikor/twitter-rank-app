import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import html

def render_follower_page(conn, df):
    # ---------------------------------------------------------
    # [CSS] 카테고리 버튼 스타일링 (알약 모양)
    # ---------------------------------------------------------
    st.markdown("""
    <style>
    /* 가로형 라디오 버튼 컨테이너 */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        gap: 8px;
    }

    /* 버튼(Label) 기본 스타일 */
    div[role="radiogroup"] label {
        background-color: #1C1F26; /* 어두운 배경 */
        border: 1px solid #2D3035;
        border-radius: 20px !important; /* 둥근 모서리 */
        padding: 6px 16px !important;
        margin-right: 0px;
        transition: all 0.2s ease;
        justify-content: center;
        width: auto !important;
    }

    /* 기본 라디오 버튼(동그라미) 숨기기 */
    div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    /* 텍스트 스타일 */
    div[role="radiogroup"] label p {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #B0B3B8 !important;
        margin: 0 !important;
    }

    /* [선택됨] 상태 스타일 */
    div[role="radiogroup"] label:has(input:checked) {
        background-color: #004A77 !important; /* 파란색 강조 */
        border-color: #004A77 !important;
    }
    
    /* [선택됨] 텍스트 색상 */
    div[role="radiogroup"] label:has(input:checked) p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* 마우스 오버 효과 */
    div[role="radiogroup"] label:hover {
        border-color: #004A77;
        background-color: #252830;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("트위터 팔로워 맵 (Follower Map)")
    
    if df.empty:
        st.info("데이터를 불러올 수 없습니다.")
        return

    # ---------------------------------------------------------
    # [UI] 카테고리 선택 & 통합 보기 토글
    # ---------------------------------------------------------
    if 'category' in df.columns:
        all_cats = ["전체보기"] + sorted(df['category'].dropna().unique().tolist())
    else:
        all_cats = ["전체보기"]

    # 기본값 설정: '크립토' 우선
    default_index = 0
    target_category = "크립토" 
    if target_category in all_cats:
        default_index = all_cats.index(target_category)

    col_cat, col_opt = st.columns([0.8, 0.2])
    
    with col_cat:
        st.write("카테고리 선택") 
        selected_category = st.radio(
            "카테고리 선택", 
            all_cats, 
            index=default_index, 
            horizontal=True, 
            label_visibility="collapsed",
            key="follower_category_main"
        )
        
    with col_opt:
        merge_categories = False
        if selected_category == "전체보기":
            st.write("") 
            st.write("") 
            merge_categories = st.toggle("통합 보기", value=False, key="follower_merge_toggle")

    st.caption(f"Twitter Follower Map - {selected_category}")
    st.write("") 

    # ---------------------------------------------------------
    # 데이터 필터링
    # ---------------------------------------------------------
    if selected_category == "전체보기":
        display_df = df[df['followers'] > 0]
    else:
        display_df = df[(df['category'] == selected_category) & (df['followers'] > 0)]

    if display_df.empty:
        st.info(f"'{selected_category}' 카테고리에 데이터가 없습니다.")
        return

    # ---------------------------------------------------------
    # 상단 요약 지표
    # ---------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    total_acc = len(display_df)
    total_fol = display_df['followers'].sum()
    top_one = display_df.loc[display_df['followers'].idxmax()] if not display_df.empty else None
    top_one_text = f"{top_one['name']}" if top_one is not None else "-"

    with col1: 
        st.markdown(f'<div class="metric-card"><div class="metric-label">전체 계정</div><div class="metric-value">{total_acc}</div></div>', unsafe_allow_html=True)
    with col2: 
        st.markdown(f'<div class="metric-card"><div class="metric-label">총 팔로워</div><div class="metric-value">{total_fol:,.0f}</div></div>', unsafe_allow_html=True)
    with col3: 
        st.markdown(f'<div class="metric-card"><div class="metric-label">최고 영향력</div><div class="metric-value" style="font-size:20px;">{top_one_text}</div></div>', unsafe_allow_html=True)
    
    st.write("")

    # ---------------------------------------------------------
    # 2. 트리맵 차트
    # ---------------------------------------------------------
    display_df['chart_label'] = display_df.apply(
        lambda x: f"{str(x['name'])}<br><span style='font-size:0.7em; font-weight:normal;'>@{str(x['handle'])}</span>", 
        axis=1
    )
    display_df['log_followers'] = np.log10(display_df['followers'].replace(0, 1))

    if merge_categories:
        display_df['root_group'] = "전체 (All)"
        path_list = ['root_group', 'chart_label']
    else:
        path_list = ['category', 'chart_label']

    fig = px.treemap(
        display_df, 
        path=path_list, 
        values='followers', 
        color='log_followers',
        custom_data=['name'], 
        color_continuous_scale=[(0.00, '#2E2B4E'), (0.05, '#353263'), (0.10, '#3F3C5C'), (0.15, '#464282'), (0.20, '#4A477A'), (0.25, '#4A5D91'), (0.30, '#4A6FA5'), (0.35, '#537CA8'), (0.40, '#5C8BAE'), (0.45, '#5C98AE'), (0.50, '#5E9CA8'), (0.55, '#5E9E94'), (0.60, '#5F9E7F'), (0.65, '#729E6F'), (0.70, '#859E5F'), (0.75, '#969E5F'), (0.80, '#A89E5F'), (0.85, '#AD905D'), (0.90, '#AE815C'), (0.95, '#AE6E5C'), (1.00, '#AE5C5C')],
        template="plotly_dark"
    )
    
    fig.update_traces(
        texttemplate='<b>%{customdata[0]}</b><br><b style="font-size:1.2em">%{value:,.0f}</b><br><span style="font-size:0.8em; color:#D1D5DB">%{percentRoot:.1%}</span>',
        textfont=dict(size=20, family="sans-serif", color="white"),
        textposition="middle center",
        marker=dict(line=dict(width=3, color='#000000')), 
        root_color="#000000",
        hovertemplate='<b>%{customdata[0]}</b><br><span style="color:#9CA3AF">@%{label}</span><br>Followers: %{value:,.0f}<br>Share: %{percentRoot:.1%}<extra></extra>'
    )
    
    fig.update_layout(
        margin=dict(t=0, l=0, r=0, b=0), 
        paper_bgcolor='#000000', plot_bgcolor='#000000', 
        height=600, 
        font=dict(family="sans-serif"), 
        coloraxis_showscale=False,
        hoverlabel=dict(bgcolor="#1C1F26", bordercolor="#10B981", font=dict(size=18, color="white"), namelength=-1)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.write("")
    
    # ---------------------------------------------------------
    # 3. 리더보드 리스트
    # ---------------------------------------------------------
    col_head, col_toggle = st.columns([1, 0.3])
    with col_head:
        st.subheader("🏆 팔로워 순위 (Leaderboard)")
    with col_toggle:
        expand_view = st.toggle("전체 펼치기", value=False, key="follower_list_toggle")
    
    ranking_df = display_df.sort_values(by='followers', ascending=False).reset_index(drop=True)
    view_total = ranking_df['followers'].sum()
    
    def clean_str(val):
        if pd.isna(val): return ""
        s = str(val).strip()
        if s.lower() == 'nan': return ""
        return s

    list_html = ""
    for index, row in ranking_df.iterrows():
        rank = index + 1
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
        img_url = f"https://unavatar.io/twitter/{row['handle']}"
        share_pct = (row['followers'] / view_total * 100) if view_total > 0 else 0
        
        recent_raw = clean_str(row.get('recent_interest', ''))
        note_raw = clean_str(row.get('note', ''))
        recent_safe = html.escape(recent_raw)
        note_safe = html.escape(note_raw)
        
        interest_html = f"<div class='rank-interest'>{recent_safe}</div>" if recent_safe else ""
        note_html = f"<span class='rank-note'>{note_safe}</span>" if note_safe else ""
        
        if 'bio' not in row: bio_content = "소개글이 없습니다."
        else: bio_content = clean_str(row['bio'])
        if not bio_content: bio_content = "소개글이 없습니다."

        # [수정됨] 마크다운 코드 블록 인식을 막기 위해 한 줄로 작성 (들여쓰기 제거)
        expanded_recent = ""
        if recent_safe:
            expanded_recent = f'<div style="margin-bottom: 12px;"><div class="bio-header" style="color: #D4E157;">📌 RECENT ACTIVITY</div><div class="bio-content" style="font-weight: 500; color: #FFFFFF;">{recent_safe}</div></div>'

        # 리스트 HTML 구성 (들여쓰기를 최소화하거나 주의해야 함)
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
                        {interest_html}
                        {note_html}
                    </div>
                    <div class="rank-stats-group">
                        <div class="rank-category">{row['category']}</div>
                        <div class="rank-share">{share_pct:.1f}%</div>
                        <div class="rank-followers">{int(row['followers']):,}</div>
                    </div>
                </div>
            </summary>
            <div class="bio-box">
                {expanded_recent}
                <div class="bio-header">📝 PROFILE BIO</div>
                <div class="bio-content">{bio_content}</div>
                <a href="https://twitter.com/{row['handle']}" target="_blank" class="bio-link-btn">
                    Visit Profile ↗
                </a>
            </div>
        </details>
        """
    
    with st.container(height=600 if not expand_view else None):
        st.markdown(list_html, unsafe_allow_html=True)
