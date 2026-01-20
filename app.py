네, 상단 요약 카드에서 **'기간'**을 제거하고, 남은 3개의 카드(전체 계정, 총 팔로워, 최고 영향력)가 화면을 꽉 채우도록 수정했습니다.

이제 상단 영역이 3등분되어 더욱 시원하게 보일 것입니다.

### ✂️ 기간 카드가 제거된 최종 `app.py`

```python
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="트위터 팔로워 맵", layout="wide")

# 2. CSS 스타일
st.markdown("""
    <style>
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #16191E; border-right: 1px solid #2D3035; }
    
    /* 상단 요약 카드 */
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    
    /* 리더보드 리스트 스타일 */
    .ranking-row { display: flex; align-items: center; justify-content: space-between; background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; padding: 12px 20px; margin-bottom: 8px; transition: all 0.2s ease; }
    .ranking-row:hover { border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); }
    
    .rank-num { font-size: 18px; font-weight: bold; color: #10B981; width: 35px; }
    .rank-img { width: 45px; height: 45px; border-radius: 50%; border: 2px solid #2D3035; margin-right: 15px; object-fit: cover; }
    
    /* 이름 및 핸들 */
    .rank-info { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }
    .rank-name { font-size: 16px; font-weight: 700; color: #FFFFFF; line-height: 1.2; }
    .rank-handle { font-size: 13px; font-weight: 400; color: #9CA3AF; line-height: 1.2; }
    
    /* 점유율(%) 스타일 */
    .rank-share { 
        font-size: 15px; 
        font-weight: 700; 
        color: #10B981; /* 강조색 (Green) */
        min-width: 70px; 
        text-align: right; 
        margin-right: 20px;
    }

    .rank-followers { font-size: 15px; font-weight: 600; color: #E5E7EB; text-align: right; min-width: 90px; }
    .rank-category { font-size: 11px; color: #9CA3AF; background-color: #374151; padding: 4px 8px; border-radius: 12px; margin-right: 15px; }
    
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
        df = conn.read(ttl="0") 
        if df is not None and not df.empty:
            df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0)
            df['category'] = df['category'].fillna('미분류') if 'category' in df.columns else '미분류'
            df['handle'] = df['handle'].astype(str)
            
            if 'name' not in df.columns:
                df['name'] = df['handle'] 
            else:
                df['name'] = df['name'].fillna(df['handle'])
                
        return df
    except: return pd.DataFrame(columns=['handle', 'name', 'followers', 'category'])
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

    # [수정] 상단 요약 카드 (4분할 -> 3분할)
    col1, col2, col3 = st.columns(3) # 컬럼을 3개로 줄임
    
    total_acc = len(display_df)
    total_fol = display_df['followers'].sum()
    top_one = display_df.loc[display_df['followers'].idxmax()] if not display_df.empty else None
    top_one_text = f"{top_one['name']}" if top_one is not None else "-"

    with col1: st.markdown(f'<div class="metric-card"><div class="metric-label">전체 계정</div><div class="metric-value">{total_acc}</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-label">총 팔로워</div><div class="metric-value">{total_fol:,.0f}</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-label">최고 영향력</div><div class="metric-value" style="font-size:20px;">{top_one_text}</div></div>', unsafe_allow_html=True)
    # 기간(7일) 카드 제거됨
    
    st.write("")

    # 메인 차트 (트리맵)
    if not display_df.empty:
        display_df['chart_label'] = display_df['name'] + "<br><span style='font-size:0.7em; font-weight:normal;'>@" + display_df['handle'] + "</span>"

        fig = px.treemap(
            display_df, 
            path=['category', 'chart_label'], 
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
            texttemplate='<b>%{label}</b><br><b style="font-size:1.2em">%{value:,.0f}</b><br><span style="font-size:0.8em; color:#D1D5DB">%{percentRoot:.1%}</span>',
            textfont=dict(size=20, family="sans-serif", color="white"),
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
        view_total = ranking_df['followers'].sum()
        
        list_html = ""
        for index, row in ranking_df.iterrows():
            rank = index + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
            img_url = f"https://unavatar.io/twitter/{row['handle']}"
            share_pct = (row['followers'] / view_total * 100) if view_total > 0 else 0
            
            list_html += f"""
            <div class="ranking-row">
                <div class="rank-num">{medal}</div>
                <img src="{img_url}" class="rank-img" onerror="this.style.display='none'">
                <div class="rank-info">
                    <div class="rank-name">{row['name']}</div>
                    <div class="rank-handle">@{row['handle']}</div>
                </div>
                <div class="rank-category">{row['category']}</div>
                <div class="rank-share">{share_pct:.1f}%</div>
                <div class="rank-followers">{int(row['followers']):,}</div>
            </div>
            """
        with st.container(height=500): st.markdown(list_html, unsafe_allow_html=True)
else: st.info("데이터가 없습니다.")

# 6. 관리자 에디터
if is_admin:
    st.divider()
    st.header("🛠️ Admin Dashboard")
    tab1, tab2 = st.tabs(["➕ 새 채널 추가", "✏️ 전체 데이터 수정"])
    
    with tab1:
        st.write("핸들과 이름을 함께 입력해주세요.")
        with st.form("add_channel_form"):
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_a:
                new_handle = st.text_input("핸들 (ID)", placeholder="예: elonmusk")
                new_name = st.text_input("표시 이름 (Name)", placeholder="예: Elon Musk")
            with col_b:
                new_followers = st.number_input("팔로워 수", min_value=0, step=100)
            with col_c:
                existing_cats = sorted(df['category'].unique().tolist())
                new_category_select = st.selectbox("카테고리", ["직접 입력"] + existing_cats, index=1 if existing_cats else 0)
                new_category_input = st.text_input("새 카테고리") if new_category_select == "직접 입력" else ""
            
            if st.form_submit_button("💾 추가하기", type="primary"):
                final_cat = new_category_input if new_category_select == "직접 입력" else new_category_select
                clean_handle = new_handle.replace("@", "").strip()
                final_name = new_name if new_name else clean_handle
                
                if clean_handle and final_cat:
                    new_data = pd.DataFrame([{'handle': clean_handle, 'name': final_name, 'followers': new_followers, 'category': final_cat}])
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    try:
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success("추가 완료!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e: st.error(f"실패: {e}")

    with tab2:
        st.write("표에서 이름을 직접 수정할 수 있습니다.")
        unique_cats = sorted(df['category'].unique().tolist())
        
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "name": st.column_config.TextColumn("표시 이름 (Name)", required=True),
                "handle": st.column_config.TextColumn("핸들 (@ID)", required=True),
                "followers": st.column_config.NumberColumn("팔로워", format="%d"),
                "category": st.column_config.SelectboxColumn("카테고리", options=unique_cats, required=True),
                "chart_label": None
            },
            key="admin_editor"
        )
        if st.button("💾 저장하기", type="primary"):
            try:
                save_df = edited_df[['handle', 'name', 'followers', 'category']]
                conn.update(worksheet="Sheet1", data=save_df)
                st.success("저장 완료!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e: st.error(f"오류: {e}")

```
