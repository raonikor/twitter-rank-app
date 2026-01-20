import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 다크 테마 커스텀 CSS 적용
st.set_page_config(page_title="Twitter Mindshare (Dark)", layout="wide")

# CSS를 사용하여 강제로 다크 모드 스타일 적용
st.markdown("""
    <style>
    .main { background-color: #0E1117; color: #FAFAFA; }
    .stSidebar { background-color: #262730; }
    .st-at { background-color: #0E1117; }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 연결 및 데이터 전처리
conn = st.connection("gsheets", type=GSheetsConnection)

def get_clean_data():
    try:
        df = conn.read(ttl="1m")
        if df is not None and not df.empty:
            # 팔로워 숫자 전처리
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            # 카테고리 전처리
            if 'category' not in df.columns:
                df['category'] = '미분류'
            else:
                df['category'] = df['category'].fillna('미분류').replace('', '미분류')
        return df
    except:
        return pd.DataFrame()

df_handles = get_clean_data()

# 3. 사이드바 구성
with st.sidebar:
    st.title("🌙 다크 모드 필터")
    
    available_cats = ["전체보기"]
    if not df_handles.empty:
        real_cats = sorted(df_handles['category'].unique().tolist())
        available_cats.extend(real_cats)
    
    selected_category = st.radio("그룹을 선택하세요", available_cats)

    # 관리자 메뉴 숨기기 (하단 배치)
    for _ in range(20): st.write("") 
    with st.expander("⚙️", expanded=False):
        admin_pw = st.text_input("System Key", type="password", label_visibility="collapsed")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 대시보드
st.title(f"📊 {selected_category} 마인드쉐어")

if not df_handles.empty:
    if selected_category == "전체보기":
        display_df = df_handles[df_handles['followers'] > 0]
    else:
        display_df = df_handles[(df_handles['category'] == selected_category) & (df_handles['followers'] > 0)]

    # 차트 출력 (다크 테마 적용)
    if not display_df.empty:
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], 
            values='followers',
            color='category',
            hover_data=['followers'],
            color_discrete_sequence=px.colors.qualitative.Set3,
            template="plotly_dark" # [핵심] 차트 배경을 어둡게 설정
        )
        fig.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("표시할 데이터가 없습니다.")
else:
    st.warning("데이터를 불러올 수 없습니다.")

# 5. 관리자 데이터 편집기
if is_admin:
    st.divider()
    st.header("🛠️ 관리자 모드 (다크)")
    edited_df = st.data_editor(df_handles, use_container_width=True, num_rows="dynamic")

    if st.button("💾 모든 수정사항 저장"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("저장 완료!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
