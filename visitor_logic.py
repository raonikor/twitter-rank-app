# visitor_logic.py
import streamlit as st
from datetime import datetime, timedelta, timezone

# 1. 방문자 수 카운트 및 업데이트 로직
def update_visitor_count(conn):
    try:
        # 캐시 없이 즉시 읽기
        v_df = conn.read(worksheet="visitors", ttl=0)
        
        # 데이터 검증
        if v_df.empty:
            st.sidebar.error("❌ 'visitors' 시트 비어있음")
            return 0, 0
        
        required_cols = {'total', 'today', 'last_date'}
        if not required_cols.issubset(v_df.columns):
            st.sidebar.error(f"❌ 헤더 오류! 필요: {required_cols}")
            return 0, 0
            
        try:
            current_total = int(str(v_df.iloc[0]['total']).replace(',', '').split('.')[0])
            current_today = int(str(v_df.iloc[0]['today']).replace(',', '').split('.')[0])
            stored_date = str(v_df.iloc[0]['last_date']).strip()
        except Exception:
            return 0, 0
        
        # 날짜 확인 (한국 시간)
        kst = timezone(timedelta(hours=9))
        today_str = datetime.now(kst).strftime("%Y-%m-%d")
        
        need_update = False
        
        # 날짜 변경 시 Today 리셋
        if stored_date != today_str:
            current_today = 0
            v_df.at[0, 'today'] = 0
            v_df.at[0, 'last_date'] = today_str
            need_update = True
        
        # 세션 체크 후 카운트 증가
        if 'visit_counted' not in st.session_state:
            current_total += 1
            current_today += 1
            v_df.at[0, 'total'] = current_total
            v_df.at[0, 'today'] = current_today
            need_update = True
            st.session_state['visit_counted'] = True
        
        # 변경사항 저장
        if need_update:
            conn.update(worksheet="visitors", data=v_df)
            
        return current_total, current_today
        
    except Exception:
        return 0, 0

# 2. 사이드바에 방문자 박스 그리기
def display_visitor_widget(total, today):
    st.markdown(f"""
        <div class="visitor-box">
            <div class="vis-label">Today</div>
            <div class="vis-val vis-today">+{today:,}</div>
            <div class="vis-divider"></div>
            <div class="vis-label">Total</div>
            <div class="vis-val vis-total">{total:,}</div>
        </div>
    """, unsafe_allow_html=True)
