import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 설정: Bridge 스타일 레이아웃
st.set_page_config(page_title="Community Mindshare", layout="wide")

# 2. [디자인 핵심] Bridge 스타일 커스텀 CSS
st.markdown("""
    <style>
    /* 전체 배경: 딥 다크 (Bridge 배경색과 유사) */
    .stApp {
        background-color: #0F1115; 
        color: #FFFFFF;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #16191E;
        border-right: 1px solid #2D3035;
    }
    
    /* 상단 메트릭 카드 디자인 (HTML/CSS로 직접 구현) */
    .metric-card {
        background-color: #1C1F26;
        border: 1px solid #2D3035;
        border-radius: 8px;
        padding: 20px;
        text-align: left;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-label {
        font-size: 14px;
        color: #9CA3AF;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .metric-delta {
        font-size: 14px;
        font-weight: 600;
    }
    .positive { color: #10B981; } /* Bridge 스타일 그린 */
    .negative { color: #EF4444; }
    
    /* 텍스트 스타일 */
    h1, h2, h3 { font-family: 'sans-serif'; color: #FFFFFF !important; }
    
    /* Plotly 차트 배경 투명화 */
    .js-plotly-plot .plotly .main-svg {
        background-color: rgba(0,0,0,0) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 전처리
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(ttl="1m")
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            if 'category' not in df.columns:
                df['category'] = '미분류'
            else:
                df['category'] = df['category'].fillna('미분류')
        return df
    except:
        return pd.DataFrame()

df = get_data()

# 4. 사이드바 메뉴 (Bridge 스타일 흉내)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/25/25231.png", width=40) # 로고 플레이스홀더
    st.markdown("### **MINDSHARE**")
    
    # 카테고리 필터
    available_cats = ["전체보기"]
    if not df.empty:
        available_cats.extend(sorted(df['category'].unique().tolist()))
    
    selected_category = st.radio(" ", available_cats, label_visibility="collapsed")
    
    st.divider()
    
    # 관리자 메뉴 (하단 배치)
    for _ in range(15): st.write("")
    with st.expander("⚙️ Admin Access", expanded=False):
        admin_pw = st.text_input("Key", type="password")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 5. 메인 대시보드 레이아웃
st.title(f"한국 커뮤니티 마인드쉐어")
st.caption(f"Korean Community Keyword Mindshare - {selected_category}")

if not df.empty:
    # 데이터 필터링
    if selected_category == "전체보기":
        display_df = df[df['followers'] > 0]
    else:
        display_df = df[(df['category'] == selected_category) & (df['followers'] > 0)]

    # [NEW] 상단 요약 메트릭 카드 섹션 (HTML 삽입)
    total_accounts = len(display_df)
    total_followers = display_df['followers'].sum()
    if not display_df.empty:
        top_handle = display_df.loc[display_df['followers'].idxmax()]['handle']
    else:
        top_handle = "-"

    # 화면을 4분할로 나눔
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">전체 계정 (Accounts)</div>
                <div class="metric-value">{total_accounts}</div>
            </div>
            """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">총 팔로워 (Total Reach)</div>
                <div class="metric-value">{total_followers:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">최고 영향력 (Top)</div>
                <div class="metric-value">{top_handle}</div>
                <div class="metric-delta positive">▲ Dominant</div>
            </div>
            """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">조회 기간</div>
                <div class="metric-value">7일</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("") # 간격

    # [NEW] 메인 트리맵 차트 (Bridge 스타일 컬러링)
    if not display_df.empty:
        # 1. 색상 매핑: Bridge 느낌의 딥한 컬러 팔레트
        custom_colors = [
            '#D97706', # Amber (BTC 느낌)
            '#2563EB', # Blue (ETH/Base 느낌)
            '#059669', # Green (Solana 느낌)
            '#DC2626', # Red
            '#7C3AED', # Purple
            '#DB2777', # Pink
            '#4B5563'  # Gray
        ]
        
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], 
            values='followers',
            color='category', # 카테고리별 색상 구분
            color_discrete_sequence=custom_colors,
            template="plotly_dark"
        )
        
        # 차트 스타일링: 모서리 느낌과 텍스트 강조
        fig.update_traces(
            textinfo="label+value",
            textfont=dict(size=20, family="Arial", color="white"),
            textposition="middle center",
            marker=dict(line=dict(width=2, color='#0F1115')), # 블록 간격(배경색과 동일하게 하여 띄워진 느낌)
            root_color="#16191E"
        )
        
        # 레이아웃 마진 제거 (꽉 차게)
        fig.update_layout(
            margin=dict(t=20, l=0, r=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            height=600 # 차트 높이 키움
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # 하단 상세 테이블 (선택사항)
        with st.expander("📋 데이터 상세 보기"):
            st.dataframe(
                display_df[['category', 'handle', 'followers']].sort_values('followers', ascending=False),
                use_container_width=True,
                hide_index=True
            )

else:
    st.info("데이터가 없습니다. 관리자 모드에서 데이터를 추가해주세요.")

# 6. 관리자 편집기 (이전 코드의 오류 수정 반영)
if is_admin:
    st.divider()
    st.header("🛠️ Admin Data Editor")
    
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")

    if st.button("Save Changes", type="primary"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("Updated!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
