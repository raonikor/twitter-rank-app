# app.py
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta, timezone

# [NEW] 분리한 모듈 불러오기
import market_logic 

# 1. 페이지 설정
st.set_page_config(page_title="Raoni Map", layout="wide")

# 2. CSS 스타일 (Raoni Map 스타일 유지)
st.markdown("""
    <style>
    /* 전체 배경 */
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    
    /* 사이드바 배경 */
    [data-testid="stSidebar"] { 
        background-color: #1E1F20; 
        border-right: 1px solid #333;
    }
    
    /* 사이드바 라디오 버튼 컨테이너 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] {
        gap: 2px;
    }

    /* 라디오 버튼의 동그라미 숨기기 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* 메뉴 항목 디자인 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        display: flex;
        width: 100%;
        padding: 6px 12px !important;
        border-radius: 8px !important;
        border: none !important;
        background-color: transparent;
        transition: all 0.2s ease;
        margin-bottom: 1px;
    }

    /* 텍스트 색상 (기본: 연회색) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label div,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label p {
        color: #B0B3B8 !important;
        font-size: 14px;
        font-weight: 500;
    }

    /* 호버 상태 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover {
        background-color: #282A2C !important;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover p {
        color: #FFFFFF !important;
    }

    /* 선택된 상태 (제미니 블루 + 흰색 글씨) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) {
        background-color: #004A77 !important;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) div,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) span {
        color: #FFFFFF !important;
        font-weight: 700;
    }

    /* 사이드바 헤더 */
    .sidebar-header {
        font-size: 11px;
        font-weight: 700;
        color: #E0E0E0;
        margin-top: 15px;
        margin-bottom: 5px;
        padding-left: 8px;
        text-transform: uppercase;
        opacity: 0.9;
    }

    /* 메인 컨텐츠 스타일 */
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    .metric-delta { font-size: 14px; font-weight: 500; margin-top: 5px; }
    .delta-up { color: #10B981; }
    .delta-down { color: #EF4444; }
    
    .ranking-row { 
        display: flex; align-items: center; justify-content: space-between; 
        background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; 
        padding: 8px 12px; margin-bottom: 6px; transition: all 0.2s ease; 
    }
    .ranking-row:hover { border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); }
    
    .rank-num { font-size: 15px; font-weight: bold; color: #10B981; width: 25px; }
    .rank-img { width: 36px; height: 36px; border-radius: 50%; border: 2px solid #2D3035; margin-right: 10px; object-fit: cover; }
    
    .rank-info { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
    .rank-name { font-size: 14px; font-weight: 700; color: #FFFFFF; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px; }
    .rank-handle { font-size: 12px; font-weight: 400; color: #9CA3AF; line-height: 1.2; }
    
    .rank-share { font-size: 13px; font-weight: 700; color: #10B981; min-width: 50px; text-align: right; margin-right: 10px; }
    .rank-followers { font-size: 13px; font-weight: 600; color: #E5E7EB; text-align: right; min-width: 70px; }
    
    .rank-category { font-size: 10px; color: #9CA3AF; background-color: #374151; padding: 2px 6px; border-radius: 8px; margin-right: 8px; display: none; }
    @media (min-width: 640px) { .rank-category { display: block; } .rank-name { max-width: 300px; } }
    
    h1, h2, h3 { font-family: 'sans-serif'; color: #FFFFFF !important; }
    .js-plotly-plot .plotly .main-svg { background-color: rgba(0,0,0,0) !important; }

    .js-plotly-plot .plotly .main-svg g.shapelayer path { transition: filter 0.2s ease; cursor: pointer; }
    .js-plotly-plot .plotly .main-svg g.shapelayer path:hover { filter: brightness(1.2) !important; opacity: 1 !important; }

    .visitor-box {
        background-color: #1C1F26;
        border: 1px solid #2D3035;
        border-radius: 12px;
        padding: 15px;
        margin-top: 20px;
        text-align: center;
    }
    .vis-label { font-size: 11px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px; }
    .vis-val { font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 5px; font-family: monospace;}
    .vis-today { color: #10B981; }
    .vis-total { color: #E5E7EB; }
    .vis-divider { height: 1px; background-color: #2D3035; margin: 8px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 방문자 처리
conn = st.connection("gsheets", type=GSheetsConnection)

# [수정된] 방문자수 로직 (디버깅 기능 추가)
def check_and_update_visitors():
    try:
        # 1. 시트 읽기 (캐시 끄기)
        v_df = conn.read(worksheet="visitors", ttl=0)
        
        # [디버깅] 시트가 비었거나 헤더가 틀린 경우 확인
        if v_df.empty:
            st.error("❌ 'visitors' 시트가 비어있습니다.")
            return 0, 0
        if not {'total', 'today', 'last_date'}.issubset(v_df.columns):
            st.error(f"❌ 헤더 오류! 현재 헤더: {v_df.columns.tolist()} -> 'total', 'today', 'last_date' 로 맞춰주세요.")
            return 0, 0
            
        # 2. 값 가져오기 (에러 방지를 위해 강제 형변환)
        # 2번째 행(index 0)의 데이터를 가져옵니다.
        try:
            current_total = int(str(v_df.iloc[0]['total']).replace(',', '').split('.')[0])
            current_today = int(str(v_df.iloc[0]['today']).replace(',', '').split('.')[0])
            stored_date = str(v_df.iloc[0]['last_date']).strip()
        except Exception as e:
            st.error(f"❌ 데이터 형식 오류: 숫자나 날짜 형식이 맞는지 확인하세요. ({e})")
            return 0, 0
        
        # 3. 날짜 비교 (한국 시간)
        kst = timezone(timedelta(hours=9))
        today_str = datetime.now(kst).strftime("%Y-%m-%d")
        
        need_update = False
        
        # 날짜가 바뀌었으면 Today 리셋
        if stored_date != today_str:
            current_today = 0
            v_df.at[0, 'today'] = 0
            v_df.at[0, 'last_date'] = today_str
            need_update = True
        
        # 4. 카운트 증가 로직 (세션 체크)
        # "새로고침"하면 세션이 유지되므로 카운트 안 됨 -> 정상
        # "새 탭/시크릿 모드"면 세션이 없으므로 카운트 됨 -> 정상
        if 'visit_counted' not in st.session_state:
            current_total += 1
            current_today += 1
            
            v_df.at[0, 'total'] = current_total
            v_df.at[0, 'today'] = current_today
            need_update = True
            
            # 방문 사실 기록
            st.session_state['visit_counted'] = True
        
        # 5. 변경사항 저장
        if need_update:
            conn.update(worksheet="visitors", data=v_df)
            
        return current_total, current_today
        
    except Exception as e:
        st.error(f"❌ 시스템 오류: {e}")
        return 0, 0

# 함수 실행
total_visitors, today_visitors = check_and_update_visitors()

@st.cache_data(ttl="30m") 
def get_sheet_data():
    try:
        df = conn.read(ttl="0") 
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            df['category'] = df['category'].fillna('미분류') if 'category' in df.columns else '미분류'
            df['handle'] = df['handle'].astype(str)
            if 'name' not in df.columns: df['name'] = df['handle'] 
            else: df['name'] = df['name'].fillna(df['handle'])
        return df
    except: return pd.DataFrame(columns=['handle', 'name', 'followers', 'category'])

# 4. 사이드바 구성 (Raoni Map 스타일)
with st.sidebar:
    st.markdown("### **Raoni Map**")
    
    st.markdown('<div class="sidebar-header">메뉴 (MENU)</div>', unsafe_allow_html=True)
    menu = st.radio(" ", ["트위터 팔로워 맵", "지수 비교 (Indices)"], label_visibility="collapsed")
    
    st.divider()
    
    if menu == "트위터 팔로워 맵":
        df = get_sheet_data()
        st.markdown('<div class="sidebar-header">카테고리 (CATEGORY)</div>', unsafe_allow_html=True)
        available_cats = ["전체보기"]
        if not df.empty: available_cats.extend(sorted(df['category'].unique().tolist()))
        selected_category = st.radio("카테고리 선택", available_cats, label_visibility="collapsed")
    
    for _ in range(3): st.write("")
    with st.expander("⚙️ 설정 (Admin)", expanded=False):
        admin_pw = st.text_input("Key", type="password")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

    st.markdown(f"""
        <div class="visitor-box">
            <div class="vis-label">Today</div>
            <div class="vis-val vis-today">+{today_visitors:,}</div>
            <div class="vis-divider"></div>
            <div class="vis-label">Total</div>
            <div class="vis-val vis-total">{total_visitors:,}</div>
        </div>
    """, unsafe_allow_html=True)

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
            display_df['log_followers'] = np.log10(display_df['followers'].replace(0, 1))
            display_df['chart_label'] = display_df['name'] + "<br><span style='font-size:0.7em; font-weight:normal;'>@" + display_df['handle'] + "</span>"

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
            st.subheader("🏆 팔로워 순위 (Leaderboard)")
            
            ranking_df = display_df.sort_values(by='followers', ascending=False).reset_index(drop=True)
            view_total = ranking_df['followers'].sum()
            
            list_html = ""
            for index, row in ranking_df.iterrows():
                rank = index + 1
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
                img_url = f"https://unavatar.io/twitter/{row['handle']}"
                share_pct = (row['followers'] / view_total * 100) if view_total > 0 else 0
                
                list_html += f"""
                <div class="ranking-row">
                    <div class="rank-num">{medal}</div>
                    <img src="{img_url}" class="rank-img" onerror="this.style.display='none'">
                    <div class="rank-info">
                        <div class="rank-name">{row['name']}</div>
                        <div class="rank-handle">@{row['handle']}</div>
                    </div>
                    <div class="rank-category">{row['category']}</div>
                    <div class="rank-share">{share_pct:.1f}%</div>
                    <div class="rank-followers">{int(row['followers']):,}</div>
                </div>
                """
            with st.container(height=500): st.markdown(list_html, unsafe_allow_html=True)
    else: st.info("데이터가 없습니다.")

# ==========================================
# [PAGE 2] 지수 비교 (Indices)
# ==========================================
elif menu == "지수 비교 (Indices)":
    # [NEW] 모듈을 통해 화면 렌더링 호출
    market_logic.render_market_page()

# 관리자 동기화 (Admin Sync)
if is_admin:
    st.divider()
    st.header("🛠️ Admin Dashboard")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 데이터 동기화 (Sync)", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2: st.write("👈 데이터를 새로고침합니다.")

