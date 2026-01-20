import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정: 다크 모드 레이아웃
st.set_page_config(page_title="Twitter Mindshare Pro", layout="wide")

# CSS: 전체적인 다크 분위기 조성
st.markdown("""
    <style>
    /* 전체 배경: 딥 다크 그레이 */
    .stApp {
        background-color: #121212; 
        color: #E0E0E0;
    }
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
        border-right: 1px solid #333333;
    }
    /* 텍스트 스타일 */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-family: 'sans-serif';
    }
    /* Expander(접는 메뉴) 배경 및 테두리 */
    .streamlit-expanderHeader {
        background-color: #2C2C2C;
        color: #FFFFFF;
        border-radius: 5px;
    }
    [data-testid="stExpander"] {
        border: 1px solid #444444;
        border-radius: 5px;
        background-color: #1E1E1E;
    }
    /* 버튼 스타일 */
    .stButton>button {
        background-color: #2C2C2C;
        color: #FFFFFF;
        border: 1px solid #555555;
    }
    .stButton>button:hover {
        background-color: #404040;
        border-color: #FFFFFF;
    }
    /* 입력창 스타일 */
    input {
        background-color: #2C2C2C !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드
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

# 3. 사이드바
with st.sidebar:
    st.title("📂 카테고리 필터")
    
    available_cats = ["전체보기"]
    if not df_handles.empty:
        real_cats = sorted(df_handles['category'].unique().tolist())
        available_cats.extend(real_cats)
    
    selected_category = st.radio("분석할 그룹 선택", available_cats)

    for _ in range(20): st.write("") 
    with st.expander("⚙️ System Admin", expanded=False):
        admin_pw = st.text_input("Access Key", type="password")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 대시보드
st.title(f"📊 {selected_category} Mindshare")

if not df_handles.empty:
    if selected_category == "전체보기":
        display_df = df_handles[df_handles['followers'] > 0]
    else:
        display_df = df_handles[(df_handles['category'] == selected_category) & (df_handles['followers'] > 0)]

    if not display_df.empty:
        # 차트: 가독성 높은 다크 모드
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], 
            values='followers',
            color='category',
            color_discrete_sequence=px.colors.qualitative.Set3,
            template="plotly_dark"
        )
        
        fig.update_traces(
            textinfo="label+value",
            textfont=dict(size=18, family="Arial"),
            marker=dict(line=dict(width=1, color='#121212')),
            root_color="#1E1E1E"
        )
        
        fig.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#E0E0E0")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # [핵심 수정] 표(Table) 스타일링: 다크 모드로 강제 변환
        st.write("") # 간격 띄우기
        with st.expander("📋 상세 데이터 리스트 보기 (Click to Open)"):
            
            # 1. 보여줄 데이터 정리 (정렬)
            table_df = display_df[['category', 'handle', 'followers']].sort_values(by='followers', ascending=False)
            
            # 2. Pandas Styler로 색상 입히기 (배경: 어둡게 / 글자: 하얗게)
            styler = table_df.style.set_properties(**{
                'background-color': '#1E1E1E', # 표 배경색 (사이드바와 동일)
                'color': '#E0E0E0',            # 글자색
                'border-color': '#444444'      # 테두리색
            }).highlight_max(axis=0, props='color: #FFD700; font-weight: bold;') # 최대값 금색 강조
            
            # 3. Streamlit에 그리기
            st.dataframe(
                styler,
                use_container_width=True,
                hide_index=True,
                height=300 # 높이 고정 (스크롤 가능)
            )
            
    else:
        st.info("표시할 데이터가 없습니다.")
else:
    st.warning("데이터를 불러오는 중입니다.")

# 5. 관리자 에디터
if is_admin:
    st.divider()
    st.header("🛠️ 데이터 마스터 편집기")
    
    # 관리자 편집기는 Streamlit 테마 설정을 따릅니다.
    # (아래 설정 팁을 참고하여 테마를 Dark로 바꾸면 자동으로 어두워집니다)
    edited_df = st.data_editor(df_handles, use_container_width=True, num_rows="dynamic")

    if st.button("💾 변경사항 저장", type="primary"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("데이터 저장 완료")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
