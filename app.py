import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 다크 테마 강제 적용
st.set_page_config(page_title="Twitter Mindshare Pro", layout="wide")

# [핵심] 다크 모드 통합 디자인 CSS
st.markdown("""
    <style>
    /* 전체 배경 및 기본 글자색 */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #1A1C24;
    }
    /* 사이드바 내 모든 텍스트 흰색 고정 */
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #FFFFFF !important;
    }
    /* 탭 메뉴 디자인 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        color: #808495;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom-color: #FFFFFF !important;
    }
    /* 입력창 배경색 조정 */
    input {
        background-color: #262730 !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 데이터 로드
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

# 3. 사이드바 (분류 필터)
with st.sidebar:
    st.markdown("## 📂 분류 필터")
    
    available_cats = ["전체보기"]
    if not df_handles.empty:
        real_cats = sorted(df_handles['category'].unique().tolist())
        available_cats.extend(real_cats)
    
    selected_category = st.radio("그룹을 선택하세요", available_cats)

    # 관리자 메뉴를 하단에 은밀하게 배치
    for _ in range(25): st.write("") 
    with st.expander("⚙️ System", expanded=False):
        admin_pw = st.text_input("Key", type="password", label_visibility="collapsed")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 화면
st.title(f"📊 {selected_category} 마인드쉐어")

if not df_handles.empty:
    if selected_category == "전체보기":
        display_df = df_handles[df_handles['followers'] > 0]
    else:
        display_df = df_handles[(df_handles['category'] == selected_category) & (df_handles['followers'] > 0)]

    if not display_df.empty:
        # 차트 템플릿을 plotly_dark로 설정하여 일체감 부여
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], 
            values='followers',
            color='category',
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("해당 카테고리에 데이터가 없습니다.")

# 5. 관리자 편집기
if is_admin:
    st.divider()
    st.header("🛠️ 마스터 데이터 관리")
    # 다크 모드용 데이터 에디터는 자동으로 테마를 따라감
    edited_df = st.data_editor(df_handles, use_container_width=True, num_rows="dynamic")

    if st.button("💾 모든 수정사항 클라우드 저장"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("데이터가 성공적으로 업데이트되었습니다!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")
