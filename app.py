import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Twitter Mindshare Dashboard", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # 시트 로드 (캐시 설정으로 속도 향상)
    return conn.read(ttl="5m")

df_handles = get_data()

# 3. 사이드바 구성 (분류 필터링)
with st.sidebar:
    st.title("📂 카테고리 필터")
    
    # 카테고리 목록 정의 (시트에 있는 카테고리 자동 추출 + '전체보기' 추가)
    categories = ["전체보기", "크립토", "정치계", "경제계", "연예/예술"]
    selected_category = st.radio("분류를 선택하세요", categories)
    
    st.divider()
    # 관리자 로그인 (사이드바 하단으로 이동 및 입력란 간소화)
    st.subheader("🔑 시스템 관리")
    pw = st.text_input("Admin Password", type="password", label_visibility="collapsed")
    is_admin = (pw == st.secrets["ADMIN_PW"])

# 4. 메인 화면 로직
st.title(f"📊 Twitter Mindshare: {selected_category}")

# 데이터 필터링 로직
if selected_category == "전체보기":
    display_df = df_handles
else:
    # 'category' 컬럼이 있는 경우에만 필터링
    if 'category' in df_handles.columns:
        display_df = df_handles[df_handles['category'] == selected_category]
    else:
        display_df = pd.DataFrame()
        st.error("구글 시트에 'category' 헤더를 추가해주세요!")

# 차트 출력
if not display_df.empty and 'followers' in display_df.columns:
    # 트리맵 시각화
    fig = px.treemap(
        display_df, 
        path=[px.Constant("전체") if selected_category == "전체보기" else 'category', 'handle'], 
        values='followers',
        color='followers',
        color_continuous_scale='Blues',
        title=f"{selected_category} 그룹 마인드쉐어 분석"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 데이터 상세 표
    st.dataframe(display_df[['handle', 'followers', 'category']], use_container_width=True)
else:
    st.warning(f"'{selected_category}' 카테고리에 등록된 데이터가 없습니다.")

# 5. 관리자 전용 화면 (로그인 시에만 아래에 나타남)
if is_admin:
    st.divider()
    st.header("🛠️ 관리자 데이터 마스터")
    
    # 엑셀처럼 수정 가능한 에디터
    st.info("💡 카테고리 칸에 '크립토', '정치계' 등을 입력하여 분류를 지정하세요.")
    edited_df = st.data_editor(
        df_handles, 
        use_container_width=True, 
        num_rows="dynamic",
        key="admin_editor"
    )

    if st.button("💾 모든 변경사항 구글 시트에 최종 저장"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("데이터가 성공적으로 업데이트되었습니다!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")
