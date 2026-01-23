import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import html

# 1. 프로젝트 데이터 가져오기 및 포인트 계산
def get_project_data(conn): 
    try:
        # 워크시트 이름: 'projects'
        df = conn.read(worksheet="projects", ttl="30m") 
        
        if df is not None and not df.empty:
            # ---------------------------------------------------------
            # [1] 컬럼 매핑 (한글/영어 호환)
            # ---------------------------------------------------------
            # 예상 컬럼: 계정(account), 언급횟수(mentions), 총조회수(views), 비고(note), 포인트(point), 카테고리(category)
            col_map = {
                '계정': 'name', 'account': 'name',
                '언급횟수': 'mentions', 'mention_count': 'mentions',
                '총조회수': 'views', 'total_views': 'views',
                '비고': 'desc', 'note': 'desc',
                '포인트': 'score', 'point': 'score',
                '카테고리': 'category', 'category': 'category'
            }
            df = df.rename(columns=col_map)
            
            # ---------------------------------------------------------
            # [2] 데이터 전처리 (숫자 변환)
            # ---------------------------------------------------------
            # 숫자형 컬럼 변환 (콤마 제거)
            for col in ['mentions', 'views', 'score']:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(',', ''), errors='coerce'
                    ).fillna(0)
                else:
                    df[col] = 0 # 컬럼 없으면 0으로 초기화

            # 텍스트 컬럼 처리
            if 'name' not in df.columns: df['name'] = "Unknown"
            df['name'] = df['name'].fillna("Unknown").astype(str).str.strip()
            
            # 트위터 핸들(@) 추출 (이름 컬럼에 같이 있거나, 핸들이라고 가정)
            # 여기서는 편의상 'name'을 핸들로 간주하고 처리
            df['handle'] = df['name'].apply(lambda x: x if x.startswith('@') else f"@{x}")
            df['clean_name'] = df['name'].str.replace('@', '') # 표시용 이름

            if 'desc' not in df.columns: df['desc'] = ""
            df['desc'] = df['desc'].fillna("")

            if 'category' not in df.columns: df['category'] = "전체"
            df['category'] = df['category'].fillna("전체")

            # ---------------------------------------------------------
            # [3] 포인트(점수) 계산 로직
            # 공식: (언급횟수 / MAX(언급)) * 40 + (총조회수 / MAX(조회수)) * 60
            # ---------------------------------------------------------
            max_mentions = df['mentions'].max()
            max_views = df['views'].max()
            
            # 분모가 0일 경우 대비
            if max_mentions == 0: max_mentions = 1
            if max_views == 0: max_views = 1
            
            # 계산 (기존 포인트 컬럼이 있어도, 수식 기준으로 재계산하여 정확도 보장)
            df['calculated_score'] = (
                (df['mentions'] / max_mentions) * 40 + 
                (df['views'] / max_views) * 60
            )
            
            # 최종 'value'는 계산된 점수 사용
            df['value'] = df['calculated_score'].round(1) # 소수점 1자리
            
        return df
    except Exception as e:
        # 에러 시 빈 프레임 반환
        return pd.DataFrame(columns=['name', 'handle', 'mentions', 'views', 'desc', 'category', 'value'])

# 2. 렌더링 함수
def render_project_page(conn):
    # ---------------------------------------------------------
    # [CSS] 스타일링 (팔로워 맵과 동일)
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
    
    df = get_project_data(conn)
    
    if df.empty:
        st.info("데이터를 불러올 수 없습니다. 'projects' 시트의 컬럼명(계정, 언급횟수, 총조회수, 비고)을 확인해주세요.")
        return

    # ---------------------------------------------------------
    # [UI] 카테고리 선택
    # ---------------------------------------------------------
    all_cats = ["전체보기"] + sorted(df['category'].unique().tolist())

    col_cat, col_opt = st.columns([0.8, 0.2])
    
    with col_cat:
        st.write("카테고리 선택") 
        selected_category = st.radio(
            "카테고리 선택", 
            all_cats, 
            horizontal=True, 
            label_visibility="collapsed",
            key="project_category_main"
        )
        
    with col_opt:
        merge_categories = False
        if selected_category == "전체보기":
            st.write("") 
            st.write("") 
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
    # 상단 요약 지표
    # ---------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    total_acc = len(display_df)
    total_mentions = display_df['mentions'].sum()
    top_one = display_df.loc[display_df['value'].idxmax()] if not display_df.empty else None
    top_name = f"{top_one['handle']}" if top_one is not None else "-"

    with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">랭킹 계정 수</div><div class="metric-value">{total_acc}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">총 언급 횟수</div><div class="metric-value">{total_mentions:,.0f}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">1위 계정 (Highest Score)</div><div class="metric-value" style="font-size:20px;">{top_name}</div></div>', unsafe_allow_html=True)
    
    st.write("")

    # ---------------------------------------------------------
    # 트리맵 차트
    # ---------------------------------------------------------
    display_df['chart_label'] = display_df.apply(
        lambda x: f"{str(x['handle'])}<br><span style='font-size:0.8em; font-weight:normal;'>{x['value']:.1f} pts</span>", 
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
        values='value', 
        color='value',
        custom_data=['handle', 'mentions', 'views', 'desc'], 
        color_continuous_scale=[(0.00, '#2E2B4E'), (0.05, '#353263'), (0.10, '#3F3C5C'), (0.15, '#464282'), (0.20, '#4A477A'), (0.25, '#4A5D91'), (0.30, '#4A6FA5'), (0.35, '#537CA8'), (0.40, '#5C8BAE'), (0.45, '#5C98AE'), (0.50, '#5E9CA8'), (0.55, '#5E9E94'), (0.60, '#5F9E7F'), (0.65, '#729E6F'), (0.70, '#859E5F'), (0.75, '#969E5F'), (0.80, '#A89E5F'), (0.85, '#AD905D'), (0.90, '#AE815C'), (0.95, '#AE6E5C'), (1.00, '#AE5C5C')],
        template="plotly_dark"
    )
    
    fig.update_traces(
        texttemplate='<b>%{customdata[0]}</b><br><b style="font-size:1.4em">%{value:.1f}</b>',
        textfont=dict(size=20, family="sans-serif", color="white"),
        textposition="middle center",
        marker=dict(line=dict(width=3, color='#000000')), 
        root_color="#000000",
        hovertemplate='<b>%{customdata[0]}</b><br>Score: %{value:.1f}<br>Mentions: %{customdata[1]:,.0f}<br>Views: %{customdata[2]:,.0f}<extra></extra>'
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
    # 리스트 뷰 (랭킹)
    # ---------------------------------------------------------
    col_head, col_toggle = st.columns([1, 0.3])
    with col_head:
        st.subheader("📋 계정 랭킹 (Account Ranking)")
    with col_toggle:
        expand_view = st.toggle("전체 펼치기", value=False, key="project_list_toggle")
    
    # 점수 높은 순 정렬
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
        
        # 프로필 이미지 (unavatar 사용)
        img_url = f"https://unavatar.io/twitter/{row['clean_name']}"
        
        # 상세 내용 (비고)
        desc_raw = clean_str(row.get('desc', ''))
        desc_safe = html.escape(desc_raw)
        
        # 통계 텍스트
        stats_text = f"🗣️ {int(row['mentions']):,} | 👁️ {int(row['views']):,}"

        list_html += f"""
        <details {'open' if expand_view else ''}>
            <summary>
                <div class="ranking-row">
                    <div class="rank-col-1">
                        <div class="rank-num">{medal}</div>
                        <img src="{img_url}" class="rank-img" onerror="this.style.display='none'">
                    </div>
                    <div class="rank-info">
                        <div class="rank-name">{row['handle']}</div>
                        <div class="rank-handle" style="font-size:11px; color:#6B7280;">{stats_text}</div>
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
                    • Mention Count: {int(row['mentions']):,}<br>
                    • Total Views: {int(row['views']):,}
                </div>
                <a href="https://twitter.com/{row['clean_name']}" target="_blank" class="bio-link-btn">
                    Visit Profile ↗
                </a>
            </div>
        </details>
        """
    
    with st.container(height=600 if not expand_view else None):
        st.markdown(list_html, unsafe_allow_html=True)
