import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="트위터 팔로워 맵", layout="wide")

# 2. CSS 스타일 (타일형 디자인 + 인터랙션 + 사이드바 메뉴)
st.markdown("""
    <style>
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #16191E; border-right: 1px solid #2D3035; }
    
    /* 상단 요약 카드 */
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    
    /* 리더보드 리스트 스타일 */
    .ranking-row { display: flex; align-items: center; justify-content: space-between; background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; padding: 10px 20px; margin-bottom: 8px; transition: all 0.2s ease; }
    .ranking-row:hover { border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); }
    
    .rank-num { font-size: 18px; font-weight: bold; color: #10B981; width: 30px; }
    .rank-img { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #2D3035; margin-right: 15px; object-fit: cover; }
    .rank-handle { font-size: 16px; font-weight: 600; color: #E5E7EB; flex-grow: 1; }
    .rank-followers { font-size: 14px; color: #9CA3AF; text-align: right; min-width: 100px; }
    .rank-category { font-size: 11px; color: #9CA3AF; background-color: #374151; padding: 2px 8px; border-radius: 12px; margin-right: 15px; }
    
    h1, h2, h3 { font-family: 'sans-serif'; color: #FFFFFF !important; }
    .js-plotly-plot .plotly .main-svg { background-color: rgba(0,0,0,0) !important; }

    /* 차트 인터랙션 */
    .js-plotly-plot .main-svg { transition: filter 0.3s ease-in-out; }
    .js-plotly-plot:hover .main-svg { filter: brightness(0.92); }
    .js-plotly-plot:active { transform: scale(0.995); transition: transform 0.1s cubic-bezier(0, 0, 0.2, 1); }

    /* 사이드바 메뉴 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; padding: 12px 15px !important; margin-bottom: 8px; transition: all 0.2s ease; color: #E5E7EB !important;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover {
        border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
conn = st.connection("gsheets", type=GSheetsConnection)
def get_data():
    try:
        df = conn.read(ttl="0") # 관리자 작업을 위해 캐시 끔 (즉시 반영 확인용)
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            df['category'] = df['category'].fillna('미분류') if 'category' in df.columns else '미분류'
            df['handle'] = df['handle'].astype(str) # 핸들은 문자열로 보장
        return df
    except: return pd.DataFrame(columns=['handle', 'followers', 'category'])
df = get_data()

# 4. 사이드바
with st.sidebar:
    st.markdown("### **MINDSHARE**")
    available_cats = ["전체보기"]
    if not df.empty: available_cats.extend(sorted(df['category'].unique().tolist()))
    selected_category = st.radio(" ", available_cats, label_visibility="collapsed")
    st.divider()
    for _ in range(15): st.write("")
    with st.expander("⚙️ Admin", expanded=False):
        admin_pw = st.text_input("Key", type="password")
        is_admin = (admin_pw == st.secrets["ADMIN_PW"])

# 5. 메인 화면
st.title(f"트위터 팔로워 맵") 
st.caption(f"Twitter Follower Map - {selected_category}")

if not df.empty:
    if selected_category == "전체보기": display_df = df[df['followers'] > 0]
    else: display_df = df[(df['category'] == selected_category) & (df['followers'] > 0)]

    # 상단 요약 카드
    col1, col2, col3, col4 = st.columns(4)
    total_acc = len(display_df)
    total_fol = display_df['followers'].sum()
    top_one = display_df.loc[display_df['followers'].idxmax()]['handle'] if not display_df.empty else "-"
    with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">전체 계정</div><div class="metric-value">{total_acc}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">총 팔로워</div><div class="metric-value">{total_fol:,.0f}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">최고 영향력</div><div class="metric-value">{top_one}</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="metric-card"><div class="metric-label">기간</div><div class="metric-value">7일</div></div>', unsafe_allow_html=True)
    st.write("")

    # 메인 차트 (트리맵)
    if not display_df.empty:
        fig = px.treemap(
            display_df, 
            path=['category', 'handle'], 
            values='followers', 
            color='followers',
            color_continuous_scale=[
                (0.0, '#3F3C5C'), (0.1, '#4A477A'), (0.2, '#4A6FA5'), (0.3, '#5C8BAE'),
                (0.4, '#5E9CA8'), (0.5, '#5F9E7F'), (0.6, '#859E5F'), (0.7, '#A89E5F'),
                (0.8, '#AE815C'), (1.0, '#AE5C5C')
            ],
            template="plotly_dark"
        )
        fig.update_traces(
            texttemplate='<b>%{label}</b><br>%{value:,.0f}<br><span style="font-size:0.8em; color:#D1D5DB">%{percentRoot:.1%}</span>',
            textfont=dict(size=24, family="sans-serif", color="white"),
            textposition="middle center",
            marker=dict(line=dict(width=6, color='#0F1115')), 
            root_color="#16191E",
            hovertemplate='<b>%{label}</b><br>Followers: %{value:,.0f}<br>Share: %{percentRoot:.1%}<extra></extra>'
        )
        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=600, font=dict(family="sans-serif"),
            hoverlabel=dict(bgcolor="#1C1F26", bordercolor="#10B981", font=dict(size=18, color="white"), namelength=-1),
            coloraxis_showscale=False 
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # 리더보드
        st.write("")
        st.subheader("🏆 팔로워 순위 (Leaderboard)")
        
        ranking_df = display_df.sort_values(by='followers', ascending=False).reset_index(drop=True)
        list_html = ""
        for index, row in ranking_df.iterrows():
            rank = index + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
            img_url = f"https://unavatar.io/twitter/{row['handle']}"
            list_html += f"""
            <div class="ranking-row">
                <div class="rank-num">{medal}</div>
                <img src="{img_url}" class="rank-img" onerror="this.style.display='none'">
                <div class="rank-category">{row['category']}</div>
                <div class="rank-handle">@{row['handle']}</div>
                <div class="rank-followers">{int(row['followers']):,} 팔로워</div>
            </div>
            """
        with st.container(height=500): st.markdown(list_html, unsafe_allow_html=True)
else: st.info("데이터가 없습니다.")

# 6. [NEW] 편리해진 관리자 에디터
if is_admin:
    st.divider()
    st.header("🛠️ Admin Dashboard")
    
    # 탭으로 기능 분리 (추가하기 vs 수정하기)
    tab1, tab2 = st.tabs(["➕ 새 채널 추가 (New)", "✏️ 전체 데이터 수정 (Edit All)"])
    
    # [기능 1] 간편 추가 폼
    with tab1:
        st.write("새로운 트위터 계정을 추가합니다. 아래 내용을 입력하고 버튼을 누르세요.")
        with st.form("add_channel_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                new_handle = st.text_input("트위터 핸들 (ID)", placeholder="예: elonmusk (@ 제외)")
                new_followers = st.number_input("팔로워 수", min_value=0, step=100)
            with col_b:
                # 기존 카테고리 목록 가져오기 + 직접 입력 옵션
                existing_cats = sorted(df['category'].unique().tolist())
                new_category_select = st.selectbox("카테고리 선택", ["직접 입력"] + existing_cats, index=1 if existing_cats else 0)
                
                new_category_input = ""
                if new_category_select == "직접 입력":
                    new_category_input = st.text_input("새 카테고리 이름 입력")
            
            submit_btn = st.form_submit_button("💾 리스트에 추가하기", type="primary")
            
            if submit_btn:
                # 데이터 정제 logic
                final_cat = new_category_input if new_category_select == "직접 입력" else new_category_select
                clean_handle = new_handle.replace("@", "").strip() # @ 제거 및 공백 제거
                
                if clean_handle and final_cat:
                    # 새 데이터 생성
                    new_data = pd.DataFrame([{'handle': clean_handle, 'followers': new_followers, 'category': final_cat}])
                    # 기존 데이터와 합치기
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    try:
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success(f"✅ @{clean_handle} 계정이 '{final_cat}' 카테고리에 성공적으로 추가되었습니다!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
                else:
                    st.warning("⚠️ 핸들과 카테고리를 모두 입력해주세요.")

    # [기능 2] 엑셀형 전체 수정 (업그레이드 버전)
    with tab2:
        st.write("데이터를 엑셀처럼 직접 수정하거나 삭제할 수 있습니다.")
        
        # 카테고리 드롭다운 설정을 위한 config 생성
        unique_cats = sorted(df['category'].unique().tolist())
        
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            # [핵심] 컬럼 설정: 카테고리를 선택상자(Dropdown)로 변경하여 오타 방지
            column_config={
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    help="카테고리를 선택하세요",
                    width="medium",
                    options=unique_cats,
                    required=True,
                ),
                "followers": st.column_config.NumberColumn(
                    "Followers",
                    min_value=0,
                    step=1,
                    format="%d", # 숫자 포맷 (콤마 없이 깔끔하게)
                ),
                "handle": st.column_config.TextColumn(
                    "Handle",
                    help="트위터 ID (@ 제외)",
                    required=True
                )
            },
            key="admin_editor"
        )

        if st.button("💾 전체 변경사항 저장 (Save Changes)", type="primary"):
            try:
                conn.update(worksheet="Sheet1", data=edited_df)
                st.success("✅ 모든 변경사항이 구글 시트에 저장되었습니다!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")
