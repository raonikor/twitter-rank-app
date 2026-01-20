import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정: 가독성을 위한 깔끔한 레이아웃
st.set_page_config(page_title="Twitter Mindshare Pro", layout="wide")

# 가독성 중심의 모던 다크 CSS
st.markdown("""
    <style>
    /* 전체 배경: 눈이 편안한 딥 다크 그레이 */
    .stApp {
        background-color: #121212; 
        color: #E0E0E0;
    }
    /* 사이드바: 메인 화면과 구분되는 톤 */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
        border-right: 1px solid #333333;
    }
    /* 텍스트 가독성 강화 */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-family: 'sans-serif';
        font-weight: 700;
    }
    p, label, .stMarkdown {
        color: #B0B0B0 !important;
        font-size: 16px;
    }
    /* 버튼 스타일: 깔끔한 강조 */
    .stButton>button {
        background-color: #2C2C2C;
        color: #FFFFFF;
        border: 1px solid #555555;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #404040;
        border-color: #FFFFFF;
    }
    /* 입력창 스타일 */
    input {
        background-color: #2C2C2C !important;
        color: #FFFFFF !important;
        border: 1px solid #444444 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 및 전처리
conn = st.connection("gsheets", type=GSheetsConnection)

def get_clean_data():
    try:
        df = conn.read(ttl="1m")
        if df is not None and not df.empty:
            # 숫자 변환 및 결측치 처리
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            if 'category' not in df.columns:
                df['category'] = '미분류'
            else:
                df['category'] = df['category'].fillna('미분류').replace('', '미분류')
        return df
    except:
        return pd.DataFrame()

df_handles = get_clean_data()

# 3. 사이드바 (깔끔한 분류)
with st.sidebar:
    st.title("📂 카테고리 필터")
    
    available_cats = ["전체보기"]
    if not df_handles.empty:
        real_cats = sorted(df_handles['category'].unique().tolist())
        available_cats.extend(real_cats)
    
    # 라디오 버튼으로 직관적인 선택
    selected_category = st.radio("분석할 그룹 선택", available_cats)

    # 관리자 메뉴 (하단 숨김 배치)
    for _ in range(20): st.write("") 
    with st.expander("⚙️ System Admin", expanded=False):
        admin_pw = st.text_input("Access Key", type="password")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 대시보드
st.title(f"📊 {selected_category} Mindshare")

if not df_handles.empty:
    # 필터링 로직
    if selected_category == "전체보기":
        display_df = df_handles[df_handles['followers'] > 0]
    else:
        display_df = df_handles[(df_handles['category'] == selected_category) & (df_handles['followers'] > 0)]

    if not display_df.empty:
        # [핵심] 가독성 높은 차트 설정
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], 
            values='followers',
            color='category',
            # 색상 팔레트: 차분하면서 구분이 잘 되는 'Set3' 사용 (눈이 안 아픔)
            color_discrete_sequence=px.colors.qualitative.Set3,
            template="plotly_dark"
        )
        
        # 차트 디테일 설정 (글자 크기, 테두리 등)
        fig.update_traces(
            textinfo="label+value", # 핸들과 숫자만 깔끔하게 표시
            textfont=dict(size=18, family="Arial"), # 폰트 키움
            marker=dict(line=dict(width=1, color='#121212')), # 블록 간 경계선 추가 (검정)
            root_color="#1E1E1E" # 배경색과 일치
        )
        
        fig.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)', # 투명 배경
            font=dict(color="#E0E0E0") # 기본 글자색 밝은 회색
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 보조 데이터 표 (접었다 펼치기 가능)
        with st.expander("📋 상세 데이터 리스트 보기"):
            st.dataframe(
                display_df[['category', 'handle', 'followers']].sort_values(by='followers', ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
    else:
        st.info("표시할 데이터가 없습니다.")
else:
    st.warning("데이터를 불러오는 중입니다.")

# 5. 관리자 에디터 (가독성 개선)
if is_admin:
    st.divider()
    st.header("🛠️ 데이터 마스터 편집기")
    st.write("아래 표에서 내용을 수정하고 **[저장]** 버튼을 누르세요.")
    
    edited_df = st.data_editor(df_handles, use_container_width=True, num_rows="dynamic")

    if st.button("💾 변경사항 구글 시트에 저장", type="primary"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("데이터가 안전하게 저장되었습니다.")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
