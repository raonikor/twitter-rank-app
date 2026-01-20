import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정: 다크 모드 및 넓은 레이아웃
st.set_page_config(page_title="Twitter Mindshare Pro", layout="wide")

# 고가독성 다크 테마 커스텀 CSS
st.markdown("""
    <style>
    /* 전체 배경: 눈이 편안한 딥 다크 그레이 */
    .stApp {
        background-color: #121212; 
        color: #E0E0E0;
    }
    /* 사이드바 스타일 */
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
    /* 버튼 및 입력창 스타일 */
    .stButton>button {
        background-color: #2C2C2C;
        color: #FFFFFF;
        border: 1px solid #555555;
    }
    input {
        background-color: #2C2C2C !important;
        color: #FFFFFF !important;
    }
    /* Expander 스타일 */
    .streamlit-expanderHeader {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 연결 및 데이터 전처리
conn = st.connection("gsheets", type=GSheetsConnection)

def get_clean_data():
    try:
        df = conn.read(ttl="1m")
        if df is not None and not df.empty:
            # [에러 방지] followers 숫자가 비어있으면 0으로 처리
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            # 카테고리 결측치 처리
            if 'category' not in df.columns:
                df['category'] = '미분류'
            else:
                df['category'] = df['category'].fillna('미분류').replace('', '미분류')
        return df
    except:
        return pd.DataFrame()

df_handles = get_clean_data()

# 3. 사이드바 구성 (분류 필터 및 숨겨진 관리자 메뉴)
with st.sidebar:
    st.markdown("### 📂 카테고리 필터")
    
    available_cats = ["전체보기"]
    if not df_handles.empty:
        real_cats = sorted(df_handles['category'].unique().tolist())
        available_cats.extend(real_cats)
    
    selected_category = st.radio("그룹을 선택하세요", available_cats)

    # 관리자 메뉴 숨기기 (하단 배치)
    for _ in range(20): st.write("") 
    with st.expander("⚙️ System Admin", expanded=False):
        admin_pw = st.text_input("Access Key", type="password", label_visibility="collapsed")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 대시보드 화면
st.title(f"📊 {selected_category} Mindshare")

if not df_handles.empty:
    # 데이터 필터링 (팔로워가 0보다 큰 데이터만 차트에 표시)
    if selected_category == "전체보기":
        display_df = df_handles[df_handles['followers'] > 0]
    else:
        display_df = df_handles[(df_handles['category'] == selected_category) & (df_handles['followers'] > 0)]

    if not display_df.empty:
        # 트리맵 차트 (가독성 최적화)
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
            marker=dict(line=dict(width=1, color='#121212')), # 블록 구분선
            root_color="#1E1E1E"
        )
        
        fig.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#E0E0E0")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 상세 데이터 표 (다크 모드 스타일 및 에러 수정 버전)
        st.write("") 
        with st.expander("📋 상세 데이터 리스트 보기 (Click to Open)"):
            table_df = display_df[['category', 'handle', 'followers']].sort_values(by='followers', ascending=False)
            
            # Pandas Styler 에러 방지 (subset 지정)
            styler = table_df.style.set_properties(**{
                'background-color': '#1E1E1E',
                'color': '#E0E0E0',
                'border-color': '#444444'
            }).highlight_max(
                axis=0, 
                subset=['followers'], # 숫자 컬럼만 계산하도록 제한
                props='color: #FFD700; font-weight: bold;'
            ).format({'followers': '{:,}'})
            
            st.dataframe(styler, use_container_width=True, hide_index=True, height=400)
            
    else:
        st.info("해당 카테고리에 데이터가 없습니다.")
else:
    st.warning("데이터를 불러올 수 없습니다. 구글 시트 설정을 확인해주세요.")

# 5. 관리자 데이터 편집기 (비밀번호 인증 시 노출)
if is_admin:
    st.divider()
    st.header("🛠️ 마스터 데이터 관리")
    st.write("표에서 직접 수정 후 저장 버튼을 누르세요. (행 추가/삭제 가능)")
    
    edited_df = st.data_editor(df_handles, use_container_width=True, num_rows="dynamic")

    if st.button("💾 모든 변경사항 저장", type="primary"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("구글 시트에 성공적으로 저장되었습니다!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
