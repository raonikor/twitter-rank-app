import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import html

# 1. 프로젝트 데이터 가져오기 및 포인트 계산
def get_project_data(conn): 
    try:
        # 캐시 없이 즉시 불러오기
        df = conn.read(worksheet="projects", ttl="0") 
        
        if df is not None and not df.empty:
            # 컬럼 매핑
            col_map = {
                '카테고리 (Category)': 'category', '계정 (Account)': 'name',
                '언급횟수 (Mentions)': 'mentions', '총조회수 (Views)': 'views',
                '비고 (Note)': 'desc',
                '카테고리': 'category', '계정': 'name', 
                '언급횟수': 'mentions', '총조회수': 'views', '비고': 'desc'
            }
            df = df.rename(columns=col_map)
            
            # 숫자형 변환 (계산용)
            for col in ['mentions', 'views']:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(',', ''), errors='coerce'
                    ).fillna(0)
                else:
                    df[col] = 0 

            # 이름/핸들 처리
            if 'name' not in df.columns: df['name'] = "Unknown"
            df['name'] = df['name'].fillna("Unknown").astype(str).str.strip()
            
            # 표준 핸들 포맷 (@붙이기)
            df['handle'] = df['name'].apply(lambda x: x if str(x).startswith('@') else f"@{x}")
            
            # [매칭 키 생성] 소문자 변환, 공백 제거, @ 제거 -> 매칭 성공률 높임
            df['join_key'] = df['handle'].astype(str).str.replace('@', '').str.strip().str.lower()

            if 'desc' not in df.columns: df['desc'] = ""
            df['desc'] = df['desc'].fillna("")

            if 'category' not in df.columns: df['category'] = "전체"
            df['category'] = df['category'].fillna("전체")

            # ---------------------------------------------------------
            # 포인트(점수) 계산 (랭킹 산정용)
            # ---------------------------------------------------------
            max_mentions = df['mentions'].max()
            max_views = df['views'].max()
            
            if max_mentions == 0: max_mentions = 1
            if max_views == 0: max_views = 1
            
            df['calculated_score'] = (
                (df['mentions'] / max_mentions) * 40 + 
                (df['views'] / max_views) * 60
            )
            df['value'] = df['calculated_score'].round(1)
            
        return df
    except Exception as e:
        return pd.DataFrame(columns=['name', 'handle', 'mentions', 'views', 'desc', 'category', 'value', 'join_key'])

# 2. 렌더링 함수
def render_project_page(conn, follower_df_raw):
    # ---------------------------------------------------------
    # [CSS] 스타일링
    # ---------------------------------------------------------
    st.markdown("""
    <style>
    div[role="radiogroup"] { display: flex; flex-direction: row; flex-wrap: wrap; gap: 8px; }
    div[role="radiogroup"] label {
        background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 20px !important;
        padding: 6px 16px !important; margin-right: 0px; transition: all 0.2s ease;
        justify-content: center; width: auto !important;
    }
    div[role="radiogroup"] label > div:first-child { display: none !important; }
    div[role="radiogroup"] label p { font-size: 14px !important; font-weight: 500 !important; color: #B0B3B8 !important; margin: 0 !important; }
    div[role="radiogroup"] label:has(input:checked) { background-color: #004A77 !important; border-color: #004A77 !important; }
    div[role="radiogroup"] label:has(input:checked) p { color: #FFFFFF !important; font-weight: 700 !important; }
    div[role="radiogroup"] label:hover { border-color: #004A77; background-color: #252830; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🧩 크립토 플젝맵 (Crypto Projects)")
    
    # 1. 프로젝트 데이터 로드
    df = get_project_data(conn)
    
    if df.empty or 'value' not in df.columns:
        st.info("데이터를 불러올 수 없습니다. 'projects' 시트를 확인해주세요.")
        return

    # ---------------------------------------------------------
    # [수정됨] 팔로워 데이터 병합 로직 (매칭 강화)
    # ---------------------------------------------------------
    df['real_name'] = df['handle'] 
    df['followers'] = 0 # 초기화

    if not follower_df_raw.empty:
        # 복사본 생성
        f_df = follower_df_raw.copy()
        
        # 팔로워 수 숫자 변환
        f_df['followers'] = pd.to_numeric(f_df['followers'], errors='coerce').fillna(0)
        
        # [매칭 키 생성] 프로젝트 데이터와 동일한 규칙 적용 (@제거, 소문자, 공백제거)
        f_df['join_key'] = f_df['handle'].astype(str).str.replace('@', '').str.strip().str.lower()
        
        # 중복 제거 (같은 핸들이면 팔로워 많은 쪽 유지)
        f_df = f_df.sort_values('followers', ascending=False).drop_duplicates('join_key')
        
        # 병합 (Left Join)
        merged = pd.merge(
            df, 
            f_df[['join_key', 'name', 'followers']], 
            on='join_key', 
            how='left',
            suffixes=('', '_map')
        )
        
        # 데이터 업데이트
        df['real_name'] = merged['name_map'].fillna(df['handle'])
        df['followers'] = merged['followers'].fillna(0)

    # ---------------------------------------------------------
    # [UI] 카테고리 선택
    # ---------------------------------------------------------
    all_cats = ["전체보기"] + sorted(df['category'].unique().tolist())

    col_cat, col_opt = st.columns([0.8, 0.2])
    with col_cat:
        st.write("카테고리 선택") 
        selected_category = st.radio(
            "카테고리 선택", all_cats, horizontal=True, label_visibility="collapsed", key="project_category_main"
        )
    with col_opt:
        merge_categories = False
        if selected_category == "전체보기":
            st.write(""); st.write("") 
            merge_categories = st.toggle("통합 보기", value=False, key="project_merge_toggle")

    st.caption(f"Crypto Project Rank - {selected_category}")
    st.write("") 

    # ---------------------------------------------------------
    # 데이터 필터링
    # ---------------------------------------------------------
    if selected_category == "전체보기":
        display_df = df[df['value'] > 0]
    else:
        display_df = df[(df['category'] == selected_category) & (df['value'] > 0)]

    if display_df.empty:
        st.info(f"'{selected_category}' 데이터가 없습니다.")
        return

    # ---------------------------------------------------------
    # 상단 요약 (조회수/언급횟수는 유지 - 전체 통계용)
    # ---------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    total_acc = len(display_df)
    total_mentions = display_df['mentions'].sum()
    
    top_one = display_df.loc[display_df['value'].idxmax()]
    top_text = f"{top_one['real_name']} ({top_one['handle']})"

    with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">랭킹 계정 수</div><div class="metric-value">{total_acc}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">총 언급 횟수</div><div class="metric-value">{total_mentions:,.0f}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">1위 계정 (Highest Score)</div><div class="metric-value" style="font-size:18px;">{top_text}</div></div>', unsafe_allow_html=True)
    
    st.write("")

    # ---------------------------------------------------------
    # 트리맵 차트
    # ---------------------------------------------------------
    display_df['chart_label'] = display_df.apply(
        lambda x: f"{str(x['real_name'])}<br><span style='font-size:0.8em; font-weight:normal;'>{x['value']:.1f} pts</span>", 
        axis=1
    )
    
    path_list = ['root_group', 'chart_label'] if merge_categories else ['category', 'chart_label']
    if merge_categories: display_df['root_group'] = "전체 (All)"

    fig = px.treemap(
        display_df, 
        path=path_list, 
        values='value', 
        color='value',
        custom_data=['real_name', 'handle', 'mentions', 'views', 'followers'],
        color_continuous_scale=[(0.00, '#2E2B4E'), (0.05, '#353263'), (0.10, '#3F3C5C'), (0.15, '#464282'), (0.20, '#4A477A'), (0.25, '#4A5D91'), (0.30, '#4A6FA5'), (0.35, '#537CA8'), (0.40, '#5C8BAE'), (0.45, '#5C98AE'), (0.50, '#5E9CA8'), (0.55, '#5E9E94'), (0.60, '#5F9E7F'), (0.65, '#729E6F'), (0.70, '#859E5F'), (0.75, '#969E5F'), (0.80, '#A89E5F'), (0.85, '#AD905D'), (0.90, '#AE815C'), (0.95, '#AE6E5C'), (1.00, '#AE5C5C')],
        template="plotly_dark"
    )
    
    fig.update_traces(
        texttemplate='<b>%{customdata[0]}</b><br><b style="font-size:1.4em">%{value:.1f}</b>',
        textfont=dict(size=20, family="sans-serif", color="white"),
        textposition="middle center",
        marker=dict(line=dict(width=3, color='#000000')), 
        # 호버 정보
        hovertemplate='<b>%{customdata[0]}</b> (%{customdata[1]})<br>Score: %{value:.1f}<br>Followers: %{customdata[4]:,.0f}<extra></extra>'
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
    # 리스트 뷰 (언급횟수, 조회수 제거됨)
    # ---------------------------------------------------------
    col_head, col_toggle = st.columns([1, 0.3])
    with col_head: st.subheader("📋 계정 랭킹 (Account Ranking)")
    with col_toggle: expand_view = st.toggle("전체 펼치기", value=False, key="project_list_toggle")
    
    ranking_df = display_df.sort_values(by='value', ascending=False).reset_index(drop=True)
    
    def clean_str(val):
        if pd.isna(val): return ""
        s = str(val).strip()
        if s.lower() == 'nan': return ""
        return s

    list_html = ""
    for index, row in ranking_df.iterrows():
        rank = index + 1
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
        
        # 이미지 URL
        clean_id = str(row['handle']).replace('@', '')
        img_url = f"https://unavatar.io/twitter/{clean_id}"
        
        desc_raw = clean_str(row.get('desc', ''))
        desc_safe = html.escape(desc_raw)
        
        # [수정] 통계 텍스트: 팔로워만 표시
        stats_text = f"👥 {int(row['followers']):,} Followers"

        list_html += f"""
        <details {'open' if expand_view else ''}>
            <summary>
                <div class="ranking-row">
                    <div class="rank-col-1">
                        <div class="rank-num">{medal}</div>
                        <img src="{img_url}" class="rank-img" onerror="this.style.display='none'">
                    </div>
                    <div class="rank-info">
                        <div class="rank-name">{row['real_name']}</div>
                        <div class="rank-handle" style="font-size:11px; color:#9CA3AF;">{row['handle']}</div>
                        <div class="rank-handle" style="font-size:11px; color:#6B7280; margin-top:2px;">{stats_text}</div>
                    </div>
                    <div class="rank-extra">
                        <span class="rank-interest" style="font-weight:400; color:#D1D5DB !important;">{desc_safe[:30]}{'...' if len(desc_safe)>30 else ''}</span>
                    </div>
                    <div class="rank-stats-group" style="width: 120px;">
                        <div class="rank-followers" style="width:100%; color:#10B981; font-size:16px;">{row['value']:.1f} pts</div>
                    </div>
                </div>
            </summary>
            <div class="bio-box">
                <div class="bio-header">📝 NOTE</div>
                <div class="bio-content">{desc_safe if desc_safe else "비고 없음"}</div>
                <div style="margin-top:10px; font-size:12px; color:#6B7280;">
                    • Followers: {int(row['followers']):,}<br>
                    </div>
                <a href="https://twitter.com/{clean_id}" target="_blank" class="bio-link-btn">
                    Visit Profile ↗
                </a>
            </div>
        </details>
        """
    
    with st.container(height=600 if not expand_view else None):
        st.markdown(list_html, unsafe_allow_html=True)
