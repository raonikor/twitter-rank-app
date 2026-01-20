import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# 1. 페이지 설정 및 다크 테마
st.set_page_config(page_title="Twitter Mindshare Admin", layout="wide")

# 핸들 목록을 저장할 파일 이름
DB_FILE = "handles.txt"
ADMIN_PASSWORD = "admin123"

# 2. 데이터 저장/불러오기 함수
def load_handles():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["elonmusk", "nasa"] # 기본값

def save_handles(handles):
    with open(DB_FILE, "w") as f:
        for h in handles:
            f.write(f"{h}\n")

# 세션 상태 초기화
if 'handle_list' not in st.session_state:
    st.session_state.handle_list = load_handles()

# 3. 사이드바 - 관리자 인증
with st.sidebar:
    st.title("🔐 관리 시스템")
    pw = st.text_input("관리자 비밀번호", type="password")
    is_admin = (pw == ADMIN_PASSWORD)
    
    if is_admin:
        st.success("관리자 모드 활성화")
    elif pw:
        st.error("비밀번호 불일치")

# 4. 메인 화면 구성
tab1, tab2 = st.tabs(["📊 실시간 마인드쉐어", "🛠️ 핸들 관리 도구"])

with tab1:
    st.header("트위터 채널 영향력 분석")
    
    if not st.session_state.handle_list:
        st.info("등록된 핸들이 없습니다. 관리자 도구에서 추가해주세요.")
    else:
        # 가상 데이터 생성 (점수 분포 최적화)
        data = pd.DataFrame({
            "채널명": [f"@{u}" for u in st.session_state.handle_list],
            "마인드쉐어": np.random.randint(5000, 100000, size=len(st.session_state.handle_list))
        }).sort_values("마인드쉐어", ascending=False)
        
        # 트리맵 시각화
        fig = px.treemap(data, path=['채널명'], values='마인드쉐어', 
                         color='마인드쉐어', color_continuous_scale='Greens')
        fig.update_layout(margin=dict(t=30, l=0, r=0, b=0))
        st.plotly_chart(fig, width='stretch')
        
        # 랭킹 테이블
        st.dataframe(data, width='stretch')

with tab2:
    if is_admin:
        st.header("🛠️ 관리자 전용 설정")
        
        # 핸들 추가
        new_h = st.text_input("추가할 트위터 ID (예: vitalikbuterin)")
        if st.button("목록에 추가"):
            if new_h and new_h not in st.session_state.handle_list:
                st.session_state.handle_list.append(new_h.strip())
                save_handles(st.session_state.handle_list) # 파일 저장
                st.success(f"@{new_h} 등록 완료")
                st.rerun() # 화면 갱신
        
        st.divider()
        
        # 핸들 삭제
        st.subheader("현재 등록된 채널")
        for h in st.session_state.handle_list:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**@{h}**")
            if c2.button("삭제", key=f"del_{h}"):
                st.session_state.handle_list.remove(h)
                save_handles(st.session_state.handle_list) # 파일 저장
                st.rerun()
    else:
        st.warning("이 탭은 관리자만 접근 가능합니다. 사이드바에서 로그인하세요.")