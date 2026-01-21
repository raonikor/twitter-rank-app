# twitter_logic.py
import streamlit as st
import streamlit.components.v1 as components

def render_twitter_page():
    st.title("🐦 실시간 트위터 (Live Feed)")
    st.caption("공식 계정의 최신 소식을 확인하세요.")

    # 1. 보고 싶은 계정 설정 (기본값: raonikor)
    # 다른 계정을 보고 싶다면 handle을 바꾸세요.
    handle = "raonikor" 
    
    # 2. 트위터 타임라인 임베드 코드 (다크 모드 적용)
    # height: 위젯 높이 (800px)
    twitter_embed_code = f"""
    <div style="display: flex; justify-content: center;">
        <a class="twitter-timeline" 
           data-theme="dark" 
           data-width="600"
           data-height="800"
           href="https://twitter.com/{handle}?ref_src=twsrc%5Etfw">
           Loading Tweets by @{handle}...
        </a> 
        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    </div>
    """

    # 3. Streamlit에 HTML 렌더링
    # scrolling=True로 해야 내부 스크롤이 자연스럽습니다.
    components.html(twitter_embed_code, height=900, scrolling=True)

    st.info("💡 트위터 정책상 로그인이 되어 있지 않으면 일부 게시물이 보이지 않을 수 있습니다.")
