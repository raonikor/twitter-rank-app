import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import html

# 1. 프로젝트 데이터 가져오기
def get_project_data(conn): 
    try:
        # 워크시트 이름: 'projects' (없으면 에러 처리됨)
        df = conn.read(worksheet="projects", ttl="30m") 
        
        if df is not None and not df.empty:
            # 수치 데이터 변환 (value 컬럼: TVL, 시총, 점수 등)
            # 만약 시트에 'value' 대신 'score'나 'tvl'이 있다면 수정 필요
            target_col = 'value' if 'value' in df.columns else df.columns[2] # 3번째 컬럼을 수치로 가정
            
            df['value'] = pd.to_numeric(
                df[target_col].astype(str).str.replace(',', ''), errors='coerce'
            ).fillna(0)
            
            df['category'] = df['category'].fillna('미분류')
            
            # ticker(티커) 또는 symbol 처리
            if 'ticker' not in df.columns: df['ticker'] = ""
            df['ticker'] = df['ticker'].astype(str).str.strip()
            
            # 이름 처리
            if 'name' not in df.columns: df['name'] = df['ticker']
            
            # 설명(desc) 처리
            if 'desc' not in df.columns: df['desc'] = ""
            else: df['desc'] = df['desc'].fillna("")
            
        return df
    except Exception as e:
        # 데이터가 없을 때 빈 프레임 반환
        return pd.DataFrame(columns=['name', 'ticker', 'value', 'category', 'desc'])

# 2. 렌더링 함수
def render_project_page(conn):
    # ---------------------------------------------------------
    # [CSS] 팔로워 맵과 동일한 알약 버튼 스타일
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
        st.info("데이터를 불러올 수 없습니다. 구글 시트에 'projects' 탭을 확인해주세요.")
        return

    # ---------------------------------------------------------
    # [UI] 카테고리 선택
    # ---------------------------------------------------------
    if 'category' in df.columns:
        all_cats = ["전체보기"] + sorted(df['category'].dropna().unique().tolist())
    else:
        all_cats = ["전체보기"]

    # 화면 분할
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

    st.caption(f"Crypto Project Map - {selected_category}")
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
    total_proj = len(display_df)
    total_val = display_df['value'].sum()
    top_one = display_df.loc[display_df['value'].idxmax()] if not display_df.empty else None
    
    # 숫자 포맷 (단위에 따라 수정 가능)
    top_text = f"{top_one['name']}" if top_one is not None else "-"

    with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">전체 프로젝트</div><div class="metric-value">{total_proj}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">총 가치(Score)</div><div class="metric-value">{total_val:,.0f}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">대장 프로젝트</div><div class="metric-value" style="font-size:20px;">{top_text}</div></div>', unsafe_allow_html=True)
    
    st.write("")

    # ---------------------------------------------------------
    # 트리맵 차트
    # ---------------------------------------------------------
    display_df['chart_label'] = display_df.apply(
        lambda x: f"{str(x['name'])}<br><span style='font-size:0.7em; font-weight:normal;'>${str(x['ticker'])}</span>", 
        axis=1
    )
    
    # 통합 보기 로직
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
        custom_data=['name', 'ticker'], 
        # 색상 팔레트 (팔로워 맵과 동일)
        color_continuous_scale=[(0.00, '#2E2B4E'), (0.05, '#353263'), (0.10, '#3F3C5C'), (0.15, '#464282'), (0.20, '#4A477A'), (0.25, '#4A5D91'), (0.30, '#4A6FA5'), (0.35, '#537CA8'), (0.40, '#5C8BAE'), (0.45, '#5C98AE'), (0.50, '#5E9CA8'), (0.55, '#5E9E94'), (0.60, '#5F9E7F'), (0.65, '#729E6F'), (0.70, '#859E5F'), (0.75, '#969E5F'), (0.80, '#A89E5F'), (0.85, '#AD905D'), (0.90, '#AE815C'), (0.95, '#AE6E5C'), (1.00, '#AE5C5C')],
        template="plotly_dark"
    )
    
    fig.update_traces(
        texttemplate='<b>%{customdata[0]}</b><br><b style="font-size:1.2em">%{value:,.0f}</b><br><span style="font-size:0.8em; color:#D1D5DB">%{percentRoot:.1%}</span>',
        textfont=dict(size=20, family="sans-serif", color="white"),
        textposition="middle center",
        marker=dict(line=dict(width=3, color='#000000')), 
        root_color="#000000",
        hovertemplate='<b>%{customdata[0]}</b> ($%{customdata[1]})<br>Value: %{value:,.0f}<br>Share: %{percentRoot:.1%}<extra></extra>'
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
    # 리스트 뷰
    # ---------------------------------------------------------
    col_head, col_toggle = st.columns([1, 0.3])
    with col_head:
        st.subheader("📋 프로젝트 랭킹 (Ranking)")
    with col_toggle:
        expand_view = st.toggle("전체 펼치기", value=False, key="project_list_toggle")
    
    ranking_df = display_df.sort_values(by='value', ascending=False).reset_index(drop=True)
    view_total = ranking_df['value'].sum()
    
    def clean_str(val):
        if pd.isna(val): return ""
        s = str(val).strip()
        if s.lower() == 'nan': return ""
        return s

    list_html = ""
    for index, row in ranking_df.iterrows():
        rank = index + 1
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
        
        # 이미지 URL (프로젝트 로고 등, 없으면 기본값 처리 필요)
        # 여기서는 Twitter 로고 서비스를 임시로 사용하거나, 빈 이미지 처리
        img_url = f"https://unavatar.io/twitter/{row['ticker']}" if row['ticker'] else ""
        
        share_pct = (row['value'] / view_total * 100) if view_total > 0 else 0
        
        # 설명글
        desc_raw = clean_str(row.get('desc', ''))
        desc_safe = html.escape(desc_raw)
        
        # 상세 내용
        detail_content = desc_safe if desc_safe else "상세 설명이 없습니다."

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
                        <div class="rank-handle">${row['ticker']}</div>
                    </div>
                    <div class="rank-extra">
                        </div>
                    <div class="rank-stats-group">
                        <div class="rank-category">{row['category']}</div>
                        <div class="rank-share">{share_pct:.1f}%</div>
                        <div class="rank-followers">{int(row['value']):,}</div>
                    </div>
                </div>
            </summary>
            <div class="bio-box">
                <div class="bio-header">ℹ️ PROJECT INFO</div>
                <div class="bio-content">{detail_content}</div>
            </div>
        </details>
        """
    
    with st.container(height=600 if not expand_view else None):
        st.markdown(list_html, unsafe_allow_html=True)
