import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Twitter Mindshare", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # 데이터 로드 및 결측치 처리
    df = conn.read(ttl="5m")
    if df is not None:
        # followers가 없거나 문자인 경우 0으로 치환
        df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
        # category가 없는 경우 '미분류'로 치환
        if 'category' not in df.columns:
            df['category'] = '미분류'
        else:
            df['category'] = df['category'].fillna('미분류')
    return df

df_handles = get_data()

# 3. 사이드바 구성
with st.sidebar:
    st.title("📂 분류 필터")
    
    # 카테고리 목록 자동 생성
    all_categories = ["전체보기", "크립토", "정치계", "경제계"]
    if df_handles is not None:
        existing_cats = df_handles['category'].unique().tolist()
        for cat in existing_cats:
            if cat not in all_categories:
                all_categories.append(cat)
    
    selected_category = st.radio("보고 싶은 그룹을 선택하세요", all_categories)

    # --- 관리자 숨기기 공간 ---
    for _ in range(20): st.write("") # 아래로 아주 멀리 밀어내기
    with st.expander("⚙️", expanded=False):
        admin_pw = st.text_input("System Key", type="password", label_visibility="collapsed")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 화면 (대시보드)
st.title(f"📊 {selected_category} 분석")

if df_handles is not None and not df_handles.empty:
    # 데이터 필터링
    if selected_category == "전체보기":
        display_df = df_handles
    else:
        display_df = df_handles[df_handles['category'] == selected_category]

    # 차트 출력 (데이터가 있는 경우에만)
    if not display_df.empty and display_df['followers'].sum() > 0:
        fig = px.treemap(
            display_df, 
            path=[px.Constant("Twitter") if selected_category == "전체보기" else 'category', 'handle'], 
            values='followers',
            color='followers',
            color_continuous_scale='Blues',
            hover_data=['followers']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"'{selected_category}' 카테고리에 숫자가 입력된 데이터가 없습니다.")
else:
    st.warning("등록된 데이터가 없습니다. 관리자 모드에서 데이터를 추가해주세요.")

# 5. 관리자 전용 편집 창 (로그인 성공 시에만 노출)
if is_admin:
    st.divider()
    st.header("🛠️ 마스터 데이터 관리")
    st.write("표 안의 내용을 직접 수정하거나 행을 추가/삭제할 수 있습니다.")
    
    # 엑셀 스타일의 데이터 편집기
    edited_df = st.data_editor(
        df_handles, 
        use_container_width=True, 
        num_rows="dynamic",
        key="main_admin_editor"
    )

    if st.button("💾 변경사항 구글 시트에 즉시 반영"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("구글 시트 업데이트 완료!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
