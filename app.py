import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Twitter Mindshare", layout="wide")

# 2. 구글 시트 연결 및 데이터 전처리
conn = st.connection("gsheets", type=GSheetsConnection)

def get_clean_data():
    df = conn.read(ttl="5m")
    if df is not None and not df.empty:
        # [에러 방지 핵심] 팔로워 숫자가 없으면(None) 0으로 변경
        df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
        # 카테고리가 없으면 '미분류'로 변경
        if 'category' not in df.columns:
            df['category'] = '미분류'
        else:
            df['category'] = df['category'].fillna('미분류')
    return df

df_handles = get_clean_data()

# 3. 사이드바 구성 (관리자 숨기기 포함)
with st.sidebar:
    st.title("📂 카테고리 필터")
    
    # 카테고리 리스트 자동 생성
    all_cats = ["전체보기"]
    if df_handles is not None:
        all_cats.extend(df_handles['category'].unique().tolist())
    
    selected_category = st.radio("그룹을 선택하세요", list(set(all_cats)))

    # 관리자 메뉴를 사이드바 맨 아래로 밀어내기
    for _ in range(25): st.write("") 
    with st.expander("⚙️", expanded=False):
        admin_pw = st.text_input("Admin Key", type="password", label_visibility="collapsed")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 4. 메인 대시보드
st.title(f"📊 {selected_category} 마인드쉐어")

if df_handles is not None and not df_handles.empty:
    # 필터링
    display_df = df_handles if selected_category == "전체보기" else df_handles[df_handles['category'] == selected_category]

    # [중요] 모든 데이터의 팔로워 합이 0보다 커야 차트가 그려짐
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
        st.info(f"'{selected_category}'에 아직 데이터가 없거나 팔로워 숫자가 모두 0입니다. 관리자 모드에서 숫자를 입력해주세요.")
else:
    st.warning("등록된 데이터가 없습니다.")

# 5. 관리자 데이터 편집기 (로그인 시 노출)
if is_admin:
    st.divider()
    st.header("🛠️ 데이터 마스터 편집기")
    st.caption("표의 칸을 더블클릭하여 수정 후 저장하세요.")
    
    edited_df = st.data_editor(df_handles, use_container_width=True, num_rows="dynamic")

    if st.button("💾 모든 수정사항 저장"):
        try:
            conn.update(worksheet="Sheet1", data=edited_df)
            st.success("저장 완료!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
