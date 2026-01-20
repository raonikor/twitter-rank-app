import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Korean Community Mindshare", layout="wide")

# 2. CSS 스타일 (이전과 동일)
st.markdown("""
    <style>
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #16191E; border-right: 1px solid #2D3035; }
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    .ranking-row { display: flex; align-items: center; justify-content: space-between; background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; padding: 15px 20px; margin-bottom: 8px; transition: all 0.2s ease; }
    .ranking-row:hover { border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); }
    .rank-num { font-size: 18px; font-weight: bold; color: #10B981; width: 40px; }
    .rank-handle { font-size: 16px; font-weight: 600; color: #E5E7EB; flex-grow: 1; padding-left: 10px; }
    .rank-followers { font-size: 16px; color: #9CA3AF; text-align: right; }
    .rank-category { font-size: 12px; color: #6B7280; background-color: #374151; padding: 2px 8px; border-radius: 12px; margin-right: 15px; }
    h1, h2, h3 { font-family: 'sans-serif'; color: #FFFFFF !important; }
    .js-plotly-plot .plotly .main-svg { background-color: rgba(0,0,0,0) !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
conn = st.connection("gsheets", type=GSheetsConnection)
def get_data():
    try:
        df = conn.read(ttl="1m")
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            df['category'] = df['category'].fillna('미분류') if 'category' in df.columns else '미분류'
        return df
    except: return pd.DataFrame()
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
st.title(f"한국 커뮤니티 마인드쉐어")
st.caption(f"Korean Community Keyword Mindshare - {selected_category}")

if not df.empty:
    if selected_category == "전체보기": display_df = df[df['followers'] > 0]
    else: display_df = df[(df['category'] == selected_category) & (df['followers'] > 0)]

    col1, col2, col3, col4 = st.columns(4)
    total_acc = len(display_df)
    total_fol = display_df['followers'].sum()
    top_one = display_df.loc[display_df['followers'].idxmax()]['handle'] if not display_df.empty else "-"
    with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">전체 계정</div><div class="metric-value">{total_acc}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">총 팔로워</div><div class="metric-value">{total_fol:,.0f}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">최고 영향력</div><div class="metric-value">{top_one}</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="metric-card"><div class="metric-label">기간</div><div class="metric-value">7일</div></div>', unsafe_allow_html=True)
    st.write("")

    # 5-2. 메인 차트 (트리맵) + 호버 효과 추가
    if not display_df.empty:
        bridge_colors = ['#D97706', '#2563EB', '#059669', '#DC2626', '#7C3AED', '#DB2777']
        fig = px.treemap(
            display_df, path=['category', 'handle'], values='followers', color='category',
            color_discrete_sequence=bridge_colors, template="plotly_dark"
        )
        fig.update_traces(
            textinfo="label+value", textfont=dict(size=24, family="sans-serif", weight="bold", color="white"),
            textposition="middle center", marker=dict(line=dict(width=3, color='#0F1115')), root_color="#16191E",
            hovertemplate='<b>%{label}</b><br>Followers: %{value:,.0f}<extra></extra>'
        )
        # [핵심 변경] 호버 툴팁 스타일링 추가
        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=600, font=dict(family="sans-serif"),
            hoverlabel=dict(
                bgcolor="#1C1F26",    # 툴팁 배경색 (카드색과 동일)
                bordercolor="#10B981", # 툴팁 테두리색 (Bridge Green 네온)
                font=dict(size=18, color="white"), # 툴팁 폰트 설정
                namelength=-1 # 긴 이름도 다 보여주기
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        st.write("")
        st.subheader("🏆 채널 랭킹 (Leaderboard)")
        ranking_df = display_df.sort_values(by='followers', ascending=False).reset_index(drop=True)
        list_html = ""
        for index, row in ranking_df.iterrows():
            rank = index + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
            list_html += f"""<div class="ranking-row"><div class="rank-num">{medal}</div><div class="rank-category">{row['category']}</div><div class="rank-handle">@{row['handle']}</div><div class="rank-followers">{int(row['followers']):,} 팔로워</div></div>"""
        with st.container(height=400): st.markdown(list_html, unsafe_allow_html=True)
else: st.info("데이터가 없습니다.")

# 6. 관리자 편집기
if is_admin:
    st.divider()
    st.header("🛠️ Admin Editor")
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    if st.button("Save", type="primary"):
        try: conn.update(worksheet="Sheet1", data=edited_df); st.success("Updated!"); st.cache_data.clear(); st.rerun()
        except Exception as e: st.error(f"Error: {e}")
