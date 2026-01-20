import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Twitter Mindshare", layout="wide")

# 2. 구글 시트 연결 및 데이터 전처리
conn = st.connection("gsheets", type=GSheetsConnection)

def get_clean_data():
    try:
        df = conn.read(ttl="1m") # 실시간 반영을 위해 1분으로 단축
        if df is not None and not df.empty:
            # [에러 방지 1] 숫자가 아닌 값은 0으로 강제 변환
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            
            # [에러 방지 2] 카테고리가 비어있으면 '미분류'로 채움
            if 'category' not in df.columns:
                df['category'] = '미분류'
            else:
                df['category'] = df['category'].fillna('미분류').replace('', '미분류')
        return df
    except:
        return pd.DataFrame()

df_handles = get_clean_data()

# 3. 사이드바 구성 (관리자 숨기기 포함)
with st.sidebar:
    st.title("📂 카테고리 필터")
    
    # 카테고리 리스트 자동 생성
    available_cats = ["전체보기"]
    if not df_handles.empty:
        real_cats = sorted(df_handles['category'].unique().tolist())
        available_cats.extend(real_cats)
    
    selected_category = st.radio("그룹을 선택하세요", available_cats)

    # 관리자 숨기기 (사이드바 하단 배치)
    for _ in range(20): st.write("") 
    with st.expander("⚙️", expanded=False):
        admin_pw = st.text_input("System Key", type="password", label_visibility="collapsed")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 대시보드
st.title(f"📊 {selected_category} 마인드쉐어")

if not df_handles.empty:
    # 데이터 필터링
    if selected_category == "전체보기":
        display_df = df_handles[df_handles['followers'] > 0] # 0인 데이터는 차트에서 제외
    else:
        display_df = df_handles[(df_handles['category'] == selected_category) & (df_handles['followers'] > 0)]

    # 차트 출력
    if not display_df.empty:
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], # 계층 구조 명확화
            values='followers',
            color='category', # 카테고리별로 색상 자동 지정
            hover_data=['followers'],
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo="label+value")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("표시할 데이터가 없습니다. 관리자 모드에서 팔로워 숫자를 입력해주세요.")
else:
    st.warning("데이터를 불러올 수 없습니다. 구글 시트 연결을 확인해주세요.")

# 5. 관리자 데이터 편집기
if is_admin:
    st.divider()
    st.header("🛠️ 데이터 마스터 편집기")
    st.caption("수정 후 아래 저장 버튼을 꼭 눌러주세요.")
    
    # 편집기에서 바로 수정 가능
    edited_df = st.data_editor(df_handles, use_container_width=True, num_rows="dynamic")

    if st.button("💾 모든 수정사항 구글 시트에 저장"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("성공적으로 저장되었습니다!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
