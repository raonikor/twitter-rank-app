import streamlit as st
import streamlit.components.v1 as components

def render_twitter_page():
    st.title("🐦 실시간 트위터 (Live Feed)")
    st.caption("Raoni (@raonikor) 공식 타임라인")

    # 레이아웃: 왼쪽(타임라인) / 오른쪽(안내 패널)
    col_feed, col_info = st.columns([0.7, 0.3])

    with col_feed:
        # [핵심] 트위터 위젯 임베드 (HTML/JS)
        # data-theme="dark"로 다크 모드 적용
        # data-height로 높이 고정
        twitter_embed_code = """
        <div style="display: flex; justify-content: center; width: 100%;">
            <a class="twitter-timeline" 
               data-theme="dark" 
               data-width="100%"
               data-height="800"
               data-chrome="noheader, nofooter, noborders, transparent"
               href="https://twitter.com/raonikor?ref_src=twsrc%5Etfw">
               Loading Tweets by Raoni...
            </a> 
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        </div>
        """
        
        # Streamlit iframe 컴포넌트로 렌더링
        components.html(twitter_embed_code, height=800, scrolling=True)

    with col_info:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Feed Info</div>
            <div class="metric-value" style="font-size: 18px;">Raoni Official</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        st.info("""
        **📢 안내**
        
        이 페이지는 실시간 X(Twitter) 피드를 보여줍니다.
        
        - 최신 트윗 확인
        - 주요 공지 사항
        - 크립토 인사이트 공유
        
        브라우저 설정에 따라 로딩에 시간이 걸릴 수 있습니다.
        """)
        
        st.write("")
        
        # 바로가기 버튼
        st.link_button("트위터 바로가기 ↗", "https://twitter.com/raonikor", use_container_width=True)
        
        st.write("")
        
        if st.button("🔄 피드 새로고침", use_container_width=True):
            st.rerun()
