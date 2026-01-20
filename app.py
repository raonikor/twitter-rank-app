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
        
        # 1. 신규 핸들 추가 섹션
        with st.expander("➕ 새 핸들 추가하기", expanded=True):
            col1, col2 = st.columns(2)
            new_h = col1.text_input("새 핸들 (예: raonikor)")
            new_f = col2.number_input("현재 팔로워 수", min_value=0, step=100)

            if st.button("구글 시트에 신규 저장"):
                if new_h:
                    try:
                        new_row = pd.DataFrame([{"handle": new_h, "followers": new_f}])
                        updated_df = pd.concat([df_handles, new_row], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success(f"@{new_h} 추가 완료!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 오류: {e}")

        st.divider()

        # 2. [핵심 추가] 기존 데이터 수정 및 삭제 섹션
        st.subheader("📝 등록된 데이터 수정 (엑셀처럼 수정하세요)")
        st.info("💡 표 안의 숫자를 더블클릭하여 수정한 후, 아래 '수정사항 저장' 버튼을 누르세요.")
        
        # 데이터 에디터 출력
        edited_df = st.data_editor(
            df_handles, 
            use_container_width=True, 
            num_rows="dynamic", # 행 삭제 및 추가 가능
            key="data_editor"
        )

        if st.button("💾 수정사항 구글 시트에 최종 저장"):
            try:
                # 수정된 데이터프레임을 구글 시트에 통째로 덮어쓰기
                conn.update(worksheet="Sheet1", data=edited_df)
                st.success("구글 시트에 성공적으로 반영되었습니다!")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"업데이트 중 오류 발생: {e}")
                
    else:
        st.warning("관리자 비밀번호를 입력하세요.")
