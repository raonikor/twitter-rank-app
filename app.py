import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta, timezone

# [모듈 사용]
import market_logic 
import visitor_logic
import event_logic 
import twitter_logic 

# 1. 페이지 설정
st.set_page_config(page_title="Raoni Map", layout="wide")

# 2. CSS 스타일 (레이아웃 깨짐 방지 & 텍스트 색상 강제 지정)
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
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label p {
        color: #B0B3B8 !important; font-size: 14px; font-weight: 500;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover { background-color: #282A2C !important; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover p { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) { background-color: #004A77 !important; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) * { color: #FFFFFF !important; font-weight: 700; }

    /* 소제목 & 방문자 박스 */
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
    
    /* 메인 컨텐츠 요소 */
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    
    /* [수정됨] 리더보드 레이아웃 고정 */
    .ranking-row { 
        display: flex; 
        align-items: center; 
        background-color: #16191E; 
        border: 1px solid #2D3035; 
        border-radius: 6px; 
        padding: 10px 15px; 
        margin-bottom: 6px; 
        transition: all 0.2s ease; 
        /* 요소 간 간격 조절 */
        gap: 15px;
    }
    .ranking-row:hover { border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); }
    
    /* 1. 등수 & 이미지 (고정폭) */
    .rank-col-1 { display: flex; align-items: center; width: 80px; flex-shrink: 0; }
    .rank-num { font-size: 15px; font-weight: bold; color: #10B981; width: 30px; text-align: center; margin-right: 5px; }
    .rank-img { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #2D3035; object-fit: cover; background-color: #333; }
    
    /* 2. 이름 & 핸들 (고정폭) */
    .rank-info { width: 150px; flex-shrink: 0; display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
    .rank-name { font-size: 15px; font-weight: 700; color: #FFFFFF !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .rank-handle { font-size: 12px; font-weight: 400; color: #9CA3AF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
    
    /* 3. 최근관심 & 비고 (남은 공간 차지) */
    .rank-extra { 
        flex-grow: 1; 
        min-width: 0; /* Flexbox 내에서 말줄임표 작동하게 함 */
        display: flex; 
        flex-direction: column; 
        justify-content: center;
    }
    .rank-interest { 
        font-size: 13px; color: #E0E7FF; font-weight: 500;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        margin-bottom: 2px;
    }
    .rank-note { 
        font-size: 11px; color: #6B7280; 
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    /* 4. 통계 정보 (우측 정렬 고정폭) */
    .rank-stats-group { 
        display: flex; align-items: center; justify-content: flex-end; width: 180px; flex-shrink: 0; 
    }
    .rank-category { font-size: 10px; color: #9CA3AF; background-color: #374151; padding: 3px 8px; border-radius: 8px; margin-right: 10px; white-space: nowrap;}
    .rank-share { font-size: 13px; font-weight: 700; color: #10B981; width: 50px; text-align: right; margin-right: 5px; }
    .rank-followers { font-size: 13px; font-weight: 600; color: #E5E7EB; width: 70px; text-align: right; }
    
    @media (max-width: 800px) { 
        .rank-category { display: none; } 
        .rank-info { width: 100px; }
        .rank-stats-group { width: 120px; }
    }
    
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
            # 1. 숫자 데이터 처리 (에러 방지)
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            
            # 2. 문자열 데이터 처리 (TypeError 방지 - 모든 텍스트 컬럼 강제 변환)
            # 없는 컬럼은 만들고, 비어있으면 빈 문자열로 채움
            cols_to_check = ['category', 'handle', 'name', 'recent_interest', 'note']
            for col in cols_to_check:
                if col not in df.columns:
                    df[col] = ''
                df[col] = df[col].fillna('').astype(str)
            
            # 이름이 없으면 핸들로 채우기
            mask = df['name'] == ''
            df.loc[mask, 'name'] = df.loc[mask, 'handle']
            
        return df
    except Exception as e:
        # 에러 발생 시 빈 데이터프레임 반환 (화면이 죽는 것 방지)
        return pd.DataFrame(columns=['handle', 'name', 'followers', 'category', 'recent_interest', 'note'])

# 4. 사이드바 구성
with st.sidebar:
    st.markdown("### **Raoni Map**")
    
    st.markdown('<div class="sidebar-header">메뉴 (MENU)</div>', unsafe_allow_html=True)
    menu = st.radio(" ", ["트위터 팔로워 맵", "실시간 트위터", "지수 비교 (Indices)", "텔레그램 이벤트"], label_visibility="collapsed")
    
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
            # [에러 방지] 문자열 결합 전 강제 형변환 보장
            display_df['chart_label'] = display_df['name'].astype(str) + "<br><span style='font-size:0.7em; font-weight:normal;'>@" + display_df['handle'].astype(str) + "</span>"
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
            st.subheader("🏆 팔로워 순위 (Leaderboard)")
            
            ranking_df = display_df.sort_values(by='followers', ascending=False).reset_index(drop=True)
            view_total = ranking_df['followers'].sum()
            
            list_html = ""
            for index, row in ranking_df.iterrows():
                rank = index + 1
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
                img_url = f"https://unavatar.io/twitter/{row['handle']}"
                share_pct = (row['followers'] / view_total * 100) if view_total > 0 else 0
                
                # 데이터 안전하게 가져오기
                recent = str(row['recent_interest']) if row['recent_interest'] else ""
                note = str(row['note']) if row['note'] else ""
                
                interest_html = f"👀 {recent}" if recent else ""
                note_html = f"📝 {note}" if note else ""

                list_html += f"""
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
                        <div class="rank-interest">{interest_html}</div>
                        <div class="rank-note">{note_html}</div>
                    </div>

                    <div class="rank-stats-group">
                        <div class="rank-category">{row['category']}</div>
                        <div class="rank-share">{share_pct:.1f}%</div>
                        <div class="rank-followers">{int(row['followers']):,}</div>
                    </div>
                </div>
                """
            with st.container(height=500): st.markdown(list_html, unsafe_allow_html=True)
    else: st.info("데이터가 없습니다.")

# ==========================================
# [PAGE 2] 실시간 트위터
# ==========================================
elif menu == "실시간 트위터":
    twitter_logic.render_twitter_page()

# ==========================================
# [PAGE 3] 지수 비교
# ==========================================
elif menu == "지수 비교 (Indices)":
    market_logic.render_market_page()

# ==========================================
# [PAGE 4] 텔레그램 이벤트
# ==========================================
elif menu == "텔레그램 이벤트":
    event_logic.render_event_page(conn)

if is_admin:
    st.divider()
    st.header("🛠️ Admin Dashboard")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 데이터 동기화 (Sync)", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2: st.write("👈 데이터를 새로고침합니다.")
