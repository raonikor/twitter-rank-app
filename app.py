import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import numpy as np
import html 
from datetime import datetime, timedelta, timezone

# [모듈 불러오기]
import market_logic 
import visitor_logic
import event_logic 
import twitter_logic
import payout_logic
import follower_logic # [NEW] 모듈 추가

# 1. 페이지 설정
st.set_page_config(page_title="Raoni Map", layout="wide")

# 2. CSS 스타일
st.markdown("""
    <style>
    /* 전체 테마 */
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1E1F20; border-right: 1px solid #333; }
    
    /* 사이드바 메뉴 스타일 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 2px; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        display: flex; width: 100%; padding: 6px 12px !important;
        border-radius: 8px !important; border: none !important;
        background-color: transparent; transition: all 0.2s ease; margin-bottom: 1px;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label div,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label span {
        color: #B0B3B8 !important; font-size: 14px; font-weight: 500;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover { background-color: #282A2C !important; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover span,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover div { 
        color: #FFFFFF !important; 
    }
    /* 선택된 메뉴 스타일 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) { 
        background-color: #004A77 !important; 
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) * { 
        color: #FFFFFF !important; font-weight: 700; 
    }

    /* 사이드바 헤더 및 위젯 */
    .sidebar-header { font-size: 11px; font-weight: 700; color: #E0E0E0; margin-top: 15px; margin-bottom: 5px; padding-left: 8px; text-transform: uppercase; opacity: 0.9; }
    .visitor-box { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 12px; padding: 15px; margin-top: 20px; text-align: center; }
    .vis-label { font-size: 11px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px; }
    .vis-val { font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 5px; font-family: monospace;}
    .vis-today { color: #10B981; }
    .vis-total { color: #E5E7EB; }
    .vis-divider { height: 1px; background-color: #2D3035; margin: 8px 0; }
    .social-box { display: flex; align-items: center; background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 12px; padding: 10px 15px; margin-top: 8px; text-decoration: none !important; transition: all 0.2s ease; cursor: pointer; }
    .social-box:hover { border-color: #10B981; background-color: #252830; transform: translateX(2px); }
    .social-img { width: 32px; height: 32px; border-radius: 50%; margin-right: 12px; border: 2px solid #2D3035; object-fit: cover; }
    .social-info { display: flex; flex-direction: column; }
    .social-label { font-size: 10px; color: #9CA3AF; margin-bottom: 0px; line-height: 1.2;}
    .social-name { font-size: 13px; font-weight: 700; color: #FFFFFF; line-height: 1.2;}
    .social-handle { font-size: 11px; color: #6B7280; }

    /* 이벤트, 메트릭 카드 */
    .event-card-link { text-decoration: none !important; }
    .event-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 10px; padding: 20px; margin-bottom: 12px; transition: all 0.2s ease; display: block; }
    .event-card:hover { border-color: #10B981; background-color: #252830; transform: translateY(-2px); }
    .event-top { display: flex; align-items: center; margin-bottom: 8px; }
    .event-badge { background-color: #004A77; color: #D3E3FD; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; margin-right: 10px; }
    .event-title { font-size: 18px; font-weight: 700; color: #FFFFFF; }
    .event-prize { font-size: 15px; color: #10B981; font-weight: 600; margin-bottom: 12px; }
    .event-bottom { display: flex; justify-content: space-between; font-size: 13px; color: #9CA3AF; border-top: 1px solid #2D3035; padding-top: 10px; }
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    
    /* 리더보드 (아코디언) */
    details > summary { list-style: none !important; outline: none !important; cursor: pointer; display: block !important; }
    details > summary::-webkit-details-marker { display: none !important; }
    details > summary::marker { display: none !important; content: ""; }
    .ranking-row { display: flex; align-items: center; background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; padding: 10px 15px; margin-bottom: 6px; transition: all 0.2s ease; gap: 15px; position: relative; }
    .ranking-row:hover { border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); }
    .rank-col-1 { display: flex; align-items: center; width: 80px; flex-shrink: 0; }
    .rank-num { font-size: 15px; font-weight: bold; color: #10B981; width: 30px; text-align: center; margin-right: 5px; }
    .rank-img { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #2D3035; object-fit: cover; background-color: #333; }
    .rank-info { width: 150px; flex-shrink: 0; display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
    .rank-name { font-size: 15px; font-weight: 700; color: #FFFFFF !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
    .rank-handle { font-size: 12px; font-weight: 400; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
    .rank-extra { flex-grow: 1; min-width: 0; min-height: 24px; display: flex; flex-direction: row; align-items: center; gap: 8px; overflow: hidden; }
    .rank-interest { font-size: 13px; color: #D4E157 !important; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 0; }
    .rank-note { font-size: 11px; color: #FFFFFF; background-color: #004A77; padding: 2px 8px; border-radius: 12px; font-weight: 600; white-space: nowrap; flex-shrink: 0; }
    .rank-stats-group { display: flex; align-items: center; justify-content: flex-end; width: 180px; flex-shrink: 0; }
    .rank-category { font-size: 10px; color: #9CA3AF; background-color: #374151; padding: 3px 8px; border-radius: 8px; margin-right: 10px; white-space: nowrap; }
    .rank-share { font-size: 13px; font-weight: 700; color: #10B981; width: 50px; text-align: right; margin-right: 5px; }
    .rank-followers { font-size: 13px; font-weight: 600; color: #E5E7EB; width: 70px; text-align: right; }
    @media (max-width: 800px) { .rank-category { display: none; } .rank-info { width: 100px; } .rank-stats-group { width: 120px; } .rank-extra { display: none; } }
    .bio-box { background-color: #15171B; border: 1px solid #2D3035; border-top: none; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; padding: 15px 20px; margin-bottom: 8px; margin-top: -2px; animation: fadeIn 0.3s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }
    .bio-header { font-size: 11px; color: #60A5FA; font-weight: 700; margin-bottom: 6px; display: flex; align-items: center; letter-spacing: 0.5px;}
    .bio-content { font-size: 14px; color: #D1D5DB; line-height: 1.6; font-weight: 400; }
    .bio-link-btn { display: inline-block; margin-top: 12px; font-size: 12px; color: #10B981; text-decoration: none; border: 1px solid #2D3035; padding: 4px 10px; border-radius: 4px; transition: all 0.2s; background-color: #1F2937; }
    .bio-link-btn:hover { background-color: #10B981; color: #FFFFFF; border-color: #10B981; }
    h1, h2, h3 { font-family: 'sans-serif'; color: #FFFFFF !important; }
    .js-plotly-plot .plotly .main-svg { background-color: rgba(0,0,0,0) !important; }
    .js-plotly-plot .plotly .main-svg g.shapelayer path { transition: filter 0.2s ease; cursor: pointer; }
    .js-plotly-plot .plotly .main-svg g.shapelayer path:hover { filter: brightness(1.2) !important; opacity: 1 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
conn = st.connection("gsheets", type=GSheetsConnection)
total_visitors, today_visitors = visitor_logic.update_visitor_count(conn)

@st.cache_data(ttl="30m") 
def get_sheet_data():
    try:
        df = conn.read(ttl="0") 
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
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
    menu_placeholder = st.empty()
    st.divider()
    for _ in range(3): st.write("")
    with st.expander("⚙️ 설정 (Admin)", expanded=False):
        admin_pw = st.text_input("Key", type="password")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])
    visitor_logic.display_visitor_widget(total_visitors, today_visitors)
    st.markdown("""
        <a href="https://x.com/raonikor" target="_blank" class="social-box">
            <img src="https://unavatar.io/twitter/raonikor" class="social-img"><div class="social-info"><div class="social-label">Made by</div><div class="social-name">Raoni</div></div>
        </a>
        <a href="https://t.me/Raoni1" target="_blank" class="social-box">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" class="social-img" style="padding:2px; background:white;"><div class="social-info"><div class="social-label">Contact</div><div class="social-name">Telegram</div></div>
        </a>
    """, unsafe_allow_html=True)

menu_options = ["트위터 팔로워 맵", "트위터 주급 맵", "실시간 트위터", "지수 비교 (Indices)", "텔레그램 이벤트"]
if is_admin: menu_options.append("관리자 페이지") 

with menu_placeholder.container():
    st.markdown('<div class="sidebar-header">메뉴 (MENU)</div>', unsafe_allow_html=True)
    menu = st.radio(" ", menu_options, label_visibility="collapsed")

# ==========================================
# [PAGE 1] 트위터 팔로워 맵
# ==========================================
if menu == "트위터 팔로워 맵":
    if 'df' not in locals() or df.empty: df = get_sheet_data()
    # [수정] 모듈 호출 (인자: conn, df)
    follower_logic.render_follower_page(conn, df)

# ==========================================
# [PAGE 2] 트위터 주급 맵
# ==========================================
elif menu == "트위터 주급 맵":
    if 'df' not in locals() or df.empty: df = get_sheet_data()
    payout_logic.render_payout_page(conn, df)

# ==========================================
# [PAGE 3] 실시간 트위터
# ==========================================
elif menu == "실시간 트위터": twitter_logic.render_twitter_page()

# ==========================================
# [PAGE 4] 지수 비교 (Indices)
# ==========================================
elif menu == "지수 비교 (Indices)": market_logic.render_market_page()

# ==========================================
# [PAGE 5] 텔레그램 이벤트
# ==========================================
elif menu == "텔레그램 이벤트": event_logic.render_event_page(conn)

# ==========================================
# [PAGE 6] 관리자 페이지
# ==========================================
elif menu == "관리자 페이지" and is_admin:
    st.title("🛠️ 관리자 대시보드"); st.info("관리자 모드"); st.divider()
    if st.button("🔄 데이터 동기화", type="primary"): st.cache_data.clear(); st.rerun()
