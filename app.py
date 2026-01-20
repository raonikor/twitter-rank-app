import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Twitter Mindshare", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    return conn.read(ttl="5m")

df_handles = get_data()

# 3. 사이드바 구성 (일반 사용자용)
with st.sidebar:
    st.title("📂 카테고리")
    # 카테고리 목록 (시트에 있는 항목 추출)
    available_cats = ["전체보기"]
    if 'category' in df_handles.columns:
        # 중복 제거 및 결측치 제외한 카테고리 리스트
        real_cats = df_handles['category'].dropna().unique().tolist()
        available_cats.extend(real_cats)
    
    selected_category = st.radio("분류를 선택하세요", available_cats)

    # --- [관리자 숨기기 영역] ---
    # 사이드바 맨 아래로 밀어내기 위해 공간 확보
    for _ in range(15): st.write("") 
    
    with st.expander("⚙️", expanded=False): # 제목을 아이콘 하나로 설정하여 숨김
        pw = st.text_input("System Key", type="password")
        is_admin = (pw == st.secrets["ADMIN_PW"])
        if is_admin:
            st.success("Admin Mode ON")

# 4. 메인 화면: 대시보드
st.title(f"📊 {selected_category} 분석")

# 데이터 필터링
if selected_category == "전체보기":
    display_df = df_handles
else:
    display_df = df_handles[df_handles['category'] == selected_category]

# 차트 출력
if not display_df.empty and 'followers' in display_df.columns:
    fig = px.treemap(
        display_df, 
        path=[px.Constant("Twitter") if selected_category == "전체보기" else 'category', 'handle'], 
        values='followers',
        color='followers',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("선택한 카테고리에 데이터가 없습니다.")

# 5. 관리자 화면 (비밀번호 통과 시에만 메인 하단에 노출)
if is_admin:
    st.divider()
    st.header("🛠️ 마스터 데이터 편집기")
    st.warning("주의: 여기서 수정하는 내용은 구글 시트에 즉시 반영됩니다.")
    
    # 수정 가능한 데이터 에디터
    edited_df = st.data_editor(
        df_handles, 
        use_container_width=True, 
        num_rows="dynamic",
        key="admin_db_editor"
    )

    if st.button("💾 변경사항 구글 시트에 최종 저장"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("데이터가 성공적으로 업데이트되었습니다!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")
