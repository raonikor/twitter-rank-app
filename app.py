import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="트위터 팔로워 맵", layout="wide")

# 2. CSS 스타일
st.markdown("""
    <style>
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #16191E; border-right: 1px solid #2D3035; }
    
    /* 상단 요약 카드 */
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    
    /* 리더보드 리스트 스타일 (슬림) */
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

    /* 차트 인터랙션 (블록 개별 강조) */
    .js-plotly-plot .plotly .main-svg g.shapelayer path {
        transition: filter 0.2s ease; cursor: pointer;
    }
    .js-plotly-plot .plotly .main-svg g.shapelayer path:hover {
        filter: brightness(1.2) !important; opacity: 1 !important;
    }

    /* 사이드바 메뉴 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; padding: 12px 15px !important; margin-bottom: 8px; transition: all 0.2s ease; color: #E5E7EB !important;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover {
        border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(ttl="30m") 
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            df['category'] = df['category'].fillna('미분류') if 'category' in df.columns else '미분류'
            df['handle'] = df['handle'].astype(str)
            
            if 'name' not in df.columns:
                df['name'] = df['handle'] 
            else:
                df['name'] = df['name'].fillna(df['handle'])
                
        return df
    except: return pd.DataFrame(columns=['handle', 'name', 'followers', 'category'])

df = get_data()

# 4. 사이드바
with st.sidebar:
    st.markdown("### **MINDSHARE**")
    available_cats = ["전체보기"]
    if not df.empty: available_cats.extend(sorted(df['category'].unique().tolist()))
    selected_category = st.radio(" ", available_cats, label_visibility="collapsed")
    st.divider()
    for _ in range(15): st.write("")
    with st.expander("⚙️ Admin", expanded=False):
        admin_pw = st.text_input("Key", type="password")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 5. 메인 화면
st.title(f"트위터 팔로워 맵") 
st.caption(f"Twitter Follower Map - {selected_category}")

if not df.empty:
    if selected_category == "전체보기": display_df = df[df['followers'] > 0]
    else: display_df = df[(df['category'] == selected_category) & (df['followers'] > 0)]

    # 상단 요약 카드
    col1, col2, col3 = st.columns(3)
    total_acc = len(display_df)
    total_fol = display_df['followers'].sum()
    top_one = display_df.loc[display_df['followers'].idxmax()] if not display_df.empty else None
    top_one_text = f"{top_one['name']}" if top_one is not None else "-"

    with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">전체 계정</div><div class="metric-value">{total_acc}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">총 팔로워</div><div class="metric-value">{total_fol:,.0f}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">최고 영향력</div><div class="metric-value" style="font-size:20px;">{top_one_text}</div></div>', unsafe_allow_html=True)
    
    st.write("")

    # 메인 차트 (트리맵)
    if not display_df.empty:
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], 
            values='followers', 
            color='followers',
            custom_data=['name'], 
            color_continuous_scale=[
                (0.0, '#3F3C5C'), (0.1, '#4A477A'), (0.2, '#4A6FA5'), (0.3, '#5C8BAE'),
                (0.4, '#5E9CA8'), (0.5, '#5F9E7F'), (0.6, '#859E5F'), (0.7, '#A89E5F'),
                (0.8, '#AE815C'), (1.0, '#AE5C5C')
            ],
            template="plotly_dark"
        )
        
        fig.update_traces(
            texttemplate='<b>%{customdata[0]}</b><br><b style="font-size:1.2em">%{value:,.0f}</b><br><span style="font-size:0.8em; color:#D1D5DB">%{percentRoot:.1%}</span>',
            textfont=dict(size=20, family="sans-serif", color="white"),
            textposition="middle center",
            
            # [핵심 변경 1] 테두리(간격) 색상을 #000000(완전 검정)으로 설정
            marker=dict(line=dict(width=2, color='#000000')), 
            
            # [핵심 변경 2] 차트 루트 배경색을 #000000(완전 검정)으로 설정
            root_color="#000000",
            
            hovertemplate='<b>%{customdata[0]}</b><br><span style="color:#9CA3AF">@%{label}</span><br>Followers: %{value:,.0f}<br>Share: %{percentRoot:.1%}<extra></extra>'
        )
        
        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0), 
            # [핵심 변경 3] 차트 전체 배경을 #000000(완전 검정)으로 설정
            paper_bgcolor='#000000', 
            plot_bgcolor='#000000', 
            height=600, 
            font=dict(family="sans-serif"),
            hoverlabel=dict(bgcolor="#1C1F26", bordercolor="#10B981", font=dict(size=18, color="white"), namelength=-1),
            coloraxis_showscale=False 
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # 리더보드
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

# 6. 관리자 대시보드
if is_admin:
    st.divider()
    st.header("🛠️ Admin Dashboard")
    st.info("데이터 관리는 구글 스프레드시트에서 직접 수행하세요.")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 데이터 동기화 (Sync)", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.write("👈 **시트 수정 후 이 버튼을 눌러야 반영됩니다.** (자동 갱신 주기: 30분)")
