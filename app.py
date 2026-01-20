import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 네온 테마 CSS 적용
st.set_page_config(page_title="Twitter Neon Dashboard", layout="wide")

# 사이버펑크 네온 스타일 CSS
st.markdown("""
    <style>
    /* 배경을 완전한 블랙으로 설정 */
    .stApp {
        background-color: #050505;
        color: #00FFD1; /* 기본 글자색: 시안 네온 */
    }
    /* 사이드바 다크그레이 & 네온 테두리 */
    [data-testid="stSidebar"] {
        background-color: #0D0D0D;
        border-right: 1px solid #FF00FF; /* 핑크 네온 구분선 */
    }
    /* 버튼 네온 효과 */
    .stButton>button {
        background-color: #000000;
        color: #00FFD1;
        border: 2px solid #00FFD1;
        box-shadow: 0 0 10px #00FFD1;
    }
    .stButton>button:hover {
        background-color: #00FFD1;
        color: #000000;
        box-shadow: 0 0 20px #00FFD1;
    }
    /* 텍스트 입력창 네온 */
    input {
        background-color: #1A1A1A !important;
        color: #FF00FF !important;
        border: 1px solid #FF00FF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_clean_data():
    try:
        df = conn.read(ttl="1m")
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            if 'category' not in df.columns:
                df['category'] = '미분류'
            else:
                df['category'] = df['category'].fillna('미분류').replace('', '미분류')
        return df
    except:
        return pd.DataFrame()

df_handles = get_clean_data()

# 3. 사이드바 (네온 스타일)
with st.sidebar:
    st.markdown("<h2 style='color: #FF00FF; text-shadow: 0 0 10px #FF00FF;'>📂 CATEGORY</h2>", unsafe_allow_html=True)
    
    available_cats = ["전체보기"]
    if not df_handles.empty:
        real_cats = sorted(df_handles['category'].unique().tolist())
        available_cats.extend(real_cats)
    
    selected_category = st.radio("필터를 선택하세요", available_cats)

    for _ in range(25): st.write("") 
    with st.expander("⚙️ System", expanded=False):
        admin_pw = st.text_input("Key", type="password", label_visibility="collapsed")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 화면
st.markdown(f"<h1 style='color: #00FFD1; text-shadow: 0 0 15px #00FFD1;'>📊 {selected_category} Mindshare</h1>", unsafe_allow_html=True)

if not df_handles.empty:
    display_df = df_handles if selected_category == "전체보기" else df_handles[df_handles['category'] == selected_category]
    display_df = display_df[display_df['followers'] > 0]

    if not display_df.empty:
        # 네온 컬러 팔레트 정의 (핑크, 시안, 라임, 옐로우)
        neon_colors = ['#FF00FF', '#00FFFF', '#ADFF2F', '#FFFF00', '#FF4500']
        
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], 
            values='followers',
            color='category',
            template="plotly_dark",
            color_discrete_sequence=neon_colors # 네온 팔레트 적용
        )
        
        # 차트 테두리 네온 효과 및 폰트 설정
        fig.update_traces(
            marker_line_width=2,
            marker_line_color="#FFFFFF",
            textinfo="label+value",
            textfont=dict(size=18, color="white", family="Courier New")
        )
        fig.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

# 5. 관리자 편집기
if is_admin:
    st.divider()
    st.markdown("<h2 style='color: #ADFF2F; text-shadow: 0 0 10px #ADFF2F;'>🛠️ ADMIN EDITOR</h2>", unsafe_allow_html=True)
    edited_df = st.data_editor(df_handles, use_container_width=True, num_rows="dynamic")

    if st.button("💾 SAVE CHANGES"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("데이터베이스 동기화 완료!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
