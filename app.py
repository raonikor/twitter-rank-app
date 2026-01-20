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
    return conn.read(ttl="10m") # 10분마다 새로고침

# 3. 데이터 로드
df_handles = get_data()
handle_list = df_handles['handle'].tolist() if not df_handles.empty else []

# --- 관리자 비밀번호 (Secrets 권장) ---
ADMIN_PASSWORD = "admin123" 

# 탭 구성
tab1, tab2 = st.tabs(["📊 대시보드", "🛠️ 관리자 설정"])

with tab1:
    st.header("트위터 마인드쉐어")
    if handle_list:
        # 가상 데이터 생성
        plot_data = pd.DataFrame({
            "채널": [f"@{h}" for h in handle_list],
            "점수": np.random.randint(1000, 50000, size=len(handle_list))
        })
        fig = px.treemap(plot_data, path=['채널'], values='점수', color='점수')
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("관리자 탭에서 핸들을 추가해주세요.")

with tab2:
    # 관리자 로그인 체크
    pw = st.sidebar.text_input("관리자 비번", type="password")
    if pw == ADMIN_PASSWORD:
        st.header("🛠️ 구글 시트 핸들 관리")
        
        # 신규 핸들 추가
        new_h = st.text_input("새 핸들 추가")
        if st.button("구글 시트에 저장"):
            if new_h and new_h not in handle_list:
                # 새 데이터 추가
                new_row = pd.DataFrame([{"handle": new_h}])
                updated_df = pd.concat([df_handles, new_row], ignore_index=True)
                
                # 구글 시트 업데이트
                conn.update(data=updated_df)
                st.success(f"@{new_h}가 구글 시트에 저장되었습니다!")
                st.rerun()
        
        st.divider()
        st.write("### 현재 등록된 리스트 (구글 시트 데이터)")
        st.dataframe(df_handles)
    else:
        st.warning("관리자 비밀번호를 입력하세요.")
