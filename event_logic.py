# event_logic.py
import streamlit as st
import pandas as pd

# 1. 이벤트 데이터 가져오기 (캐시 10분)
@st.cache_data(ttl="10m")
def get_event_data(data):
    # data는 app.py에서 conn.read()로 가져온 데이터프레임을 받습니다.
    try:
        if data is None or data.empty:
            return pd.DataFrame()
        
        # 필수 컬럼 확인
        required_cols = ['event_name', 'prizes', 'deadline', 'announce_date', 'link']
        if not set(required_cols).issubset(data.columns):
            st.error(f"❌ 'events' 시트 헤더 오류! 필요 컬럼: {required_cols}")
            return pd.DataFrame()
            
        # 결측치 처리 (빈칸은 공백으로)
        data = data.fillna("")
        return data
    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return pd.DataFrame()

# 2. 이벤트 페이지 렌더링
def render_event_page(conn):
    st.title("🎉 텔레그램 이벤트 (Telegram Events)")
    st.caption("진행 중인 다양한 이벤트에 참여해보세요!")

    try:
        # 시트 데이터 읽기
        raw_df = conn.read(worksheet="events", ttl="10m")
        df = get_event_data(raw_df)

        if not df.empty:
            # 마감기한 순으로 정렬 (선택사항)
            # df = df.sort_values(by='deadline') 

            # 카드 리스트 생성
            for index, row in df.iterrows():
                link = row['link']
                name = row['event_name']
                prizes = row['prizes']
                deadline = row['deadline']
                announce = row['announce_date']

                # HTML 카드 디자인
                st.markdown(f"""
                <a href="{link}" target="_blank" class="event-card-link">
                    <div class="event-card">
                        <div class="event-top">
                            <span class="event-badge">진행중</span>
                            <div class="event-title">{name}</div>
                        </div>
                        <div class="event-middle">
                            <div class="event-prize">🎁 {prizes}</div>
                        </div>
                        <div class="event-bottom">
                            <div class="event-date">📅 마감: {deadline}</div>
                            <div class="event-date">📢 발표: {announce}</div>
                        </div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
        else:
            st.info("현재 진행 중인 이벤트가 없습니다.")
            
    except Exception as e:
        st.error("이벤트 목록을 불러오지 못했습니다. 구글 시트 'events' 탭을 확인해주세요.")
