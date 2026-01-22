import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import numpy as np
import html # 특수문자 깨짐 방지
from datetime import datetime, timedelta, timezone

# [모듈 불러오기]
import market_logic 
import visitor_logic
import event_logic 
import twitter_logic
import payout_logic 

# 1. 페이지 설정
st.set_page_config(page_title="Raoni Map", layout="wide")

# 2. CSS 스타일
st.markdown("""
    <style>
    /* 전체 테마 */
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1E1F20; border-right: 1px solid #333; }
    
    /* 사이드바 메뉴 스타일 (알약 모양) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 2px; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child { display: none !important; }
    
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        display: flex; width: 100%; padding: 6px 12px !important;
        border-radius: 8px !important; border: none !important;
        background-color: transparent; transition: all 0.2s ease; margin-bottom: 1px;
    }

    /* 기본 상태 텍스트 색상 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label div,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label span {
        color: #B0B3B8 !important; font-size: 14px; font-weight: 500;
    }

    /* 호버 상태 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover { background-color: #282A2C !important; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover span,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover div { 
        color: #FFFFFF !important; 
    }
    
    /* [선택된 메뉴] 스타일 (흰색 글씨 강제 적용) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) { 
        background-color: #004A77 !important; 
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) * { 
        color: #FFFFFF !important; font-weight: 700; 
    }

    /* 사이드바 소제목 & 방문자 위젯 */
    .sidebar-header { font-size: 11px; font-weight: 700; color: #E0E0E0; margin-top: 15px; margin-bottom: 5px; padding-left: 8px; text-transform: uppercase; opacity: 0.9; }
    .visitor-box { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 12px; padding: 15px; margin-top: 20px; text-align: center; }
    .vis-label { font-size: 11px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px; }
    .vis-val { font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 5px; font-family: monospace;}
    .vis-today { color: #10B981; }
    .vis-total { color: #E5E7EB; }
    .vis-divider { height: 1px; background-color: #2D3035; margin: 8px 0; }

    /* 소셜 링크 박스 */
    .social-box {
        display: flex; align-items: center; background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 12px; padding: 10px 15px; margin-top: 8px;
        text-decoration: none !important; transition: all 0.2s ease; cursor: pointer;
    }
    .social-box:hover { border-color: #10B981; background-color: #252830; transform: translateX(2px); }
    .social-img { width: 32px; height: 32px; border-radius: 50%; margin-right: 12px; border: 2px solid #2D3035; object-fit: cover; }
    .social-info { display: flex; flex-direction: column; }
    .social-label { font-size: 10px; color: #9CA3AF; margin-bottom: 0px; line-height: 1.2;}
    .social-name { font-size: 13px; font-weight: 700; color: #FFFFFF; line-height: 1.2;}
    .social-handle { font-size: 11px; color: #6B7280; }

    /* 이벤트 카드 */
    .event-card-link { text-decoration: none !important; }
    .event-card {
        background-color: #1C1F26;
        border: 1px solid #2D3035;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        display: block;
    }
    .event-card:hover { border-color: #10B981; background-color: #252830; transform: translateY(-2px); }
    .event-top { display: flex; align-items: center; margin-bottom: 8px; }
    .event-badge { background-color: #004A77; color: #D3E3FD; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; margin-right: 10px; }
    .event-title { font-size: 18px; font-weight: 700; color: #FFFFFF; }
    .event-prize { font-size: 15px; color: #10B981; font-weight: 600; margin-bottom: 12px; }
    .event-bottom { display: flex; justify-content: space-between; font-size: 13px; color: #9CA3AF; border-top: 1px solid #2D3035; padding-top: 10px; }
    
    /* 상단 요약 카드 */
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    
    /* [수정] 리더보드 (아코디언) 스타일 - 화살표 완벽 제거 */
    details > summary { 
        list-style: none !important; 
        outline: none !important; 
        cursor: pointer; 
        display: block !important; 
    }
    details > summary::-webkit-details-marker { display: none !important; }
    details > summary::marker { display: none !important; content: ""; }

    /* 리더보드 행 디자인 */
    .ranking-row { 
        display: flex; align-items: center; 
        background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; 
        padding: 10px 15px; margin-bottom: 6px; 
        transition: all 0.2s ease; 
        gap: 15px;
        position: relative;
    }
    .ranking-row:hover { border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); }
    
    .rank-col-1 { display: flex; align-items: center; width: 80px; flex-shrink: 0; }
    .rank-num { font-size: 15px; font-weight: bold; color: #10B981; width: 30px; text-align: center; margin-right: 5px; }
    .rank-img { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #2D3035; object-fit: cover; background-color: #333; }
    
    .rank-info { width: 150px; flex-shrink: 0; display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
    .rank-name { font-size: 15px; font-weight: 700; color: #FFFFFF !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
    .rank-handle { font-size: 12px; font-weight: 400; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3;}
    
    /* 요약 & 비고 1줄 배치 */
    .rank-extra { 
        flex-grow: 1; 
        min-width: 0; 
        min-height: 24px;
        display: flex; 
        flex-direction: row; 
        align-items: center; 
        gap: 8px; 
        overflow: hidden;
    }
    
    /* 1. 최근 관심 */
    .rank-interest { 
        font-size: 13px; 
        color: #D4E157 !important; 
        font-weight: 700; 
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        margin-bottom: 0;
    }
    
    /* 2. 비고 */
    .rank-note { 
        font-size: 11px; 
        color: #FFFFFF; 
        background-color: #004A77; 
        padding: 2px 8px; 
        border-radius: 12px; 
        font-weight: 600;
        white-space: nowrap; 
        flex-shrink: 0; 
    }

    .rank-stats-group { display: flex; align-items: center; justify-content: flex-end; width: 180px; flex-shrink: 0; }
    .rank-category { font-size: 10px; color: #9CA3AF; background-color: #374151; padding: 3px 8px; border-radius: 8px; margin-right: 10px; white-space: nowrap;}
    .rank-share { font-size: 13px; font-weight: 700; color: #10B981; width: 50px; text-align: right; margin-right: 5px; }
    .rank-followers { font-size: 13px; font-weight: 600; color: #E5E7EB; width: 70px; text-align: right; }
    
    @media (max-width: 800px) { .rank-category { display: none; } .rank-info { width: 100px; } .rank-stats-group { width: 120px; } .rank-extra { display: none; } }
    
    /* Bio (소개글) 박스 스타일 */
    .bio-box {
        background-color: #15171B;
        border: 1px solid #2D3035; border-top: none; 
        border-bottom-left-radius: 6px; border-bottom-right-radius: 6px;
        padding: 15px 20px; margin-bottom: 8px; margin-top: -2px; 
        animation: fadeIn 0.3s ease-in-out;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }
    
    .bio-header { font-size: 11px; color: #60A5FA; font-weight: 700; margin-bottom: 6px; display: flex; align-items: center; letter-spacing: 0.5px;}
    .bio-content { font-size: 14px; color: #D1D5DB; line-height: 1.6; font-weight: 400; }
    .bio-link-btn {
        display: inline-block; margin-top: 12px; font-size: 12px; 
        color: #10B981; text-decoration: none; border: 1px solid #2D3035; 
        padding: 4px 10px; border-radius: 4px; transition: all 0.2s; background-color: #1F2937;
    }
    .bio-link-btn:hover { background-color: #10B981; color: #FFFFFF; border-color: #10B981; }
    
    h1, h2, h3 { font-family: 'sans-serif'; color: #FFFFFF !important; }
    .js-plotly-plot .plotly .main-svg { background-color: rgba(0,0,0,0) !important; }
    .js-plotly-plot .plotly .main-svg g.shapelayer path { transition: filter 0.2s ease; cursor: pointer; }
    .js-plotly-plot .plotly .main-svg g.shapelayer path:hover { filter: brightness(1.2) !important; opacity: 1 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
conn = st.connection("gsheets", type=GSheetsConnection)

# [모듈 사용] 방문자 수 계산
total_visitors, today_visitors = visitor_logic.update_visitor_count(conn)

@st.cache_data(ttl="30m") 
def get_sheet_data():
    try:
        df = conn.read(ttl="0") 
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            
            # [중요] 모든 텍스트 컬럼 강제 초기화
            cols_to_check = ['handle', 'name', 'category', 'recent_interest', 'note']
            for col in cols_to_check:
                if col not in df.columns: df[col] = "" 
                df[col] = df[col].fillna("").astype(str)
            
            mask = (df['name'] == "") | (df['name'] == "nan")
            df.loc[mask, 'name'] = df.loc[mask, 'handle']
            
        return df
    except: return pd.DataFrame(columns=['handle', 'name', 'followers', 'category', 'recent_interest', 'note'])

# 4. 사이드바 구성
with st.sidebar:
    st.markdown("### **Raoni Map**")
    
    # [설정] 메뉴가 들어갈 빈 공간을 미리 확보
    menu_placeholder = st.empty()
    
    st.divider()
    
    # 카테고리 필터 (공통 공간)
    category_placeholder = st.empty()
    
    for _ in range(3): st.write("")
    
    # [관리자 로그인 섹션] - 사이드바 하단
    with st.expander("⚙️ 설정 (Admin)", expanded=False):
        admin_pw = st.text_input("Key", type="password")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

    # 방문자 위젯
    visitor_logic.display_visitor_widget(total_visitors, today_visitors)

    # 소셜 링크
    st.markdown("""
        <a href="https://x.com/raonikor" target="_blank" class="social-box">
            <img src="https://unavatar.io/twitter/raonikor" class="social-img">
            <div class="social-info">
                <div class="social-label">Made by</div>
                <div class="social-name">Raoni</div>
            </div>
        </a>
        <a href="https://t.me/Raoni1" target="_blank" class="social-box">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" class="social-img" style="padding:2px; background:white;">
            <div class="social-info">
                <div class="social-label">Contact</div>
                <div class="social-name">Telegram</div>
            </div>
        </a>
    """, unsafe_allow_html=True)

# [핵심 로직] 메뉴 구성
menu_options = ["트위터 팔로워 맵", "트위터 주급 맵", "실시간 트위터", "지수 비교 (Indices)", "텔레그램 이벤트"]
if is_admin:
    menu_options.append("관리자 페이지") 

# [메뉴 렌더링]
with menu_placeholder.container():
    st.markdown('<div class="sidebar-header">메뉴 (MENU)</div>', unsafe_allow_html=True)
    menu = st.radio(" ", menu_options, label_visibility="collapsed")

# [카테고리 필터 렌더링] 메뉴에 따라 필터 내용 변경
selected_category = "전체보기" # 기본값

if menu == "트위터 팔로워 맵":
    df = get_sheet_data()
    with category_placeholder.container():
        st.markdown('<div class="sidebar-header">카테고리 (CATEGORY)</div>', unsafe_allow_html=True)
        available_cats = ["전체보기"]
        if not df.empty: available_cats.extend(sorted(df['category'].unique().tolist()))
        selected_category = st.radio("카테고리 선택", available_cats, label_visibility="collapsed", key="follower_cat")

elif menu == "트위터 주급 맵":
    # 주급 데이터 불러와서 카테고리 추출
    p_df = payout_logic.get_payout_data(conn)
    with category_placeholder.container():
        st.markdown('<div class="sidebar-header">카테고리 (CATEGORY)</div>', unsafe_allow_html=True)
        p_cats = ["전체보기"]
        if not p_df.empty:
            p_cats.extend(sorted(p_df['category'].unique().tolist()))
        selected_category = st.radio("카테고리 선택", p_cats, label_visibility="collapsed", key="payout_cat")
        
        # [NEW] 전체보기일 때 통합 보기 토글 표시
        merge_categories = False
        if selected_category == "전체보기":
            st.write("") 
            merge_categories = st.toggle("카테고리 통합 보기", value=False)


# ==========================================
# [PAGE 1] 트위터 팔로워 맵
# ==========================================
if menu == "트위터 팔로워 맵":
    st.title(f"트위터 팔로워 맵") 
    st.caption(f"Twitter Follower Map - {selected_category}")

    if not df.empty:
        if selected_category == "전체보기": display_df = df[df['followers'] > 0]
        else: display_df = df[(df['category'] == selected_category) & (df['followers'] > 0)]

        col1, col2, col3 = st.columns(3)
        total_acc = len(display_df)
        total_fol = display_df['followers'].sum()
        top_one = display_df.loc[display_df['followers'].idxmax()] if not display_df.empty else None
        top_one_text = f"{top_one['name']}" if top_one is not None else "-"

        with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">전체 계정</div><div class="metric-value">{total_acc}</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">총 팔로워</div><div class="metric-value">{total_fol:,.0f}</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">최고 영향력</div><div class="metric-value" style="font-size:20px;">{top_one_text}</div></div>', unsafe_allow_html=True)
        
        st.write("")

        if not display_df.empty:
            # 차트 라벨
            display_df['chart_label'] = display_df.apply(
                lambda x: f"{str(x['name'])}<br><span style='font-size:0.7em; font-weight:normal;'>@{str(x['handle'])}</span>", 
                axis=1
            )
            display_df['log_followers'] = np.log10(display_df['followers'].replace(0, 1))

            fig = px.treemap(
                display_df, 
                path=['category', 'chart_label'], 
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
                margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='#000000', plot_bgcolor='#000000', height=600, 
                font=dict(family="sans-serif"), coloraxis_showscale=False,
                hoverlabel=dict(bgcolor="#1C1F26", bordercolor="#10B981", font=dict(size=18, color="white"), namelength=-1)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            st.write("")
            
            # 토글 버튼
            col_head, col_toggle = st.columns([1, 0.3])
            with col_head:
                st.subheader("🏆 팔로워 순위 (Leaderboard)")
            with col_toggle:
                expand_view = st.toggle("전체 펼치기", value=False)
            
            ranking_df = display_df.sort_values(by='followers', ascending=False).reset_index(drop=True)
            view_total = ranking_df['followers'].sum()
            
            # 데이터 정제 함수
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
                
                # bio 내용
                if 'bio' not in row: bio_content = "소개글이 없습니다."
                else: bio_content = clean_str(row['bio'])
                if not bio_content: bio_content = "소개글이 없습니다."

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
    else: st.info("데이터가 없습니다.")

# ==========================================
# [PAGE 2] 트위터 주급 맵 (NEW)
# ==========================================
elif menu == "트위터 주급 맵":
    # 팔로워 데이터가 로드되어 있는지 확인하고 전달
    if 'df' not in locals() or df.empty:
        df = get_sheet_data()
    
    # merge_categories 변수가 위에서 정의되었으므로 전달 가능
    # (혹시 변수가 없을 경우를 대비해 기본값 처리)
    if 'merge_categories' not in locals(): merge_categories = False
        
    payout_logic.render_payout_page(conn, df, selected_category, merge_categories)

# ==========================================
# [PAGE 3] 실시간 트위터
# ==========================================
elif menu == "실시간 트위터":
    twitter_logic.render_twitter_page()

# ==========================================
# [PAGE 4] 지수 비교 (Indices)
# ==========================================
elif menu == "지수 비교 (Indices)":
    market_logic.render_market_page()

# ==========================================
# [PAGE 5] 텔레그램 이벤트
# ==========================================
elif menu == "텔레그램 이벤트":
    event_logic.render_event_page(conn)

# ==========================================
# [PAGE 6] 관리자 페이지 (Admin Only)
# ==========================================
elif menu == "관리자 페이지" and is_admin:
    st.title("🛠️ 관리자 대시보드 (Admin Dashboard)")
    st.info(f"관리자 모드로 접속 중입니다.")
    
    st.divider()
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 데이터 동기화 (Sync)", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2: st.write("👈 구글 시트 데이터를 즉시 새로고침합니다.")
