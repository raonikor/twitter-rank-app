import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Twitter Rank DB", layout="wide")

# 2. 구글 시트 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 불러오기 함수
def get_data():
    return conn.read(ttl="10m") 

# 3. 데이터 로드
df_handles = get_data()
handle_list = df_handles['handle'].tolist() if not df_handles.empty else []

# --- 관리자 비밀번호 ---
ADMIN_PASSWORD = st.secrets["ADMIN_PW"]

# 탭 구성
tab1, tab2 = st.tabs(["📊 대시보드", "🛠️ 관리자 설정"])

with tab1:
    st.header("트위터 마인드쉐어 (실제 팔로워 기반)")
    if not df_handles.empty and 'followers' in df_handles.columns:
        # 가상 데이터 대신 구글 시트의 'followers' 데이터를 사용함
        plot_data = df_handles.copy()
        plot_data['채널'] = plot_data['handle'].apply(lambda x: f"@{x}")
        
        # 트리맵 시각화 (values에 실제 팔로워 숫자를 넣음)
        fig = px.treemap(plot_data, path=['채널'], values='followers', color='followers', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("데이터가 없거나 'followers' 컬럼이 생성되지 않았습니다. 관리자 탭에서 핸들을 추가해주세요.")

with tab2:
    pw = st.sidebar.text_input("관리자 비번", type="password")
    if pw == ADMIN_PASSWORD:
        st.header("🛠️ 채널 및 팔로워 관리")
        
        # [수정 부분] 핸들과 팔로워 숫자를 동시에 입력받음
        col1, col2 = st.columns(2)
        new_h = col1.text_input("새 핸들 추가 (예: raonikor)")
        new_f = col2.number_input("현재 팔로워 수", min_value=0, step=100)

        if st.button("구글 시트에 저장"):
            if new_h and new_h not in handle_list:
                try:
                    # [수정 부분] followers 정보까지 포함하여 새 행 생성
                    new_row = pd.DataFrame([{"handle": new_h, "followers": new_f}])
                    updated_df = pd.concat([df_handles, new_row], ignore_index=True)
                    
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    st.success(f"@{new_h} (팔로워: {new_f:,}) 추가 완료!")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"저장 중 오류 발생: {e}")
        
        st.divider()
        st.write("### 현재 등록된 데이터")
        st.dataframe(df_handles, use_container_width=True)
    else:
        st.warning("관리자 비밀번호를 입력하세요.")
