import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta, timezone

# [핵심] 분리한 지수 비교 모듈 불러오기
import market_logic 

# 1. 페이지 설정
st.set_page_config(page_title="Raoni Map", layout="wide")

# 2. CSS 스타일 (Raoni Map 스타일 + 흰색 글씨 강제 적용)
st.markdown("""
    <style>
    /* 전체 배경 */
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    
    /* 사이드바 배경 */
    [data-testid="stSidebar"] { 
        background-color: #1E1F20; 
        border-right: 1px solid #333;
    }
    
    /* 사이드바 라디오 버튼 컨테이너 (간격 최소화) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] {
        gap: 2px;
    }

    /* 라디오 버튼의 동그라미 숨기기 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* [기본 상태] 메뉴 항목 디자인 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        display: flex;
        width: 100%;
        padding: 6px 12px !important;
        border-radius: 8px !important;
        border: none !important;
        background-color: transparent;
        transition: all 0.2s ease;
        margin-bottom: 1px;
    }

    /* [기본 상태] 텍스트 색상 (밝은 회색) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label div,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label p {
        color: #B0B3B8 !important;
        font-size: 14px;
        font-weight: 500;
    }

    /* [호버 상태] 마우스 올렸을 때 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover {
        background-color: #282A2C !important;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover p {
        color: #FFFFFF !important;
    }

    /* [선택된 상태] 배경색 변경 (제미니 블루) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) {
        background-color: #004A77 !important;
    }

    /* [선택된 상태] 텍스트 색상 강제 흰색 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) div,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) span {
        color: #FFFFFF !important;
        font-weight: 700;
    }

    /* 사이드바 헤더 (소제목) 스타일 */
    .sidebar-header {
        font-size: 11px;
        font-weight: 700;
        color: #E0E0E0;
        margin-top: 15px;
        margin-bottom: 5px;
        padding-left: 8px;
        text-transform: uppercase;
        opacity: 0.9;
    }

    /* 메인 컨텐츠 스타일 */
    .metric-card { background-color: #1C1F26; border: 1px solid #2D3035; border-radius: 8px; padding: 20px; text-align: left; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .metric-label { font-size: 14px; color: #9CA3AF; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; }
    
    .ranking-row { 
        display: flex; align-items: center; justify-content: space-between; 
        background-color: #16191E; border: 1px solid #2D3035; border-radius: 6px; 
        padding: 8px 12px; margin-bottom: 6px; transition: all 0.2s ease; 
    }
    .ranking-row:hover { border-color: #10B981; background-color: #1C1F26; transform: translateX(5px); }
    
    .rank-num { font-size: 15px; font-weight: bold; color: #10B981; width: 25px; }
    .rank-img { width: 36px; height: 36px; border-radius: 50%; border: 2px solid #2D3035; margin-right: 10px; object-fit: cover; }
    
    .rank-info { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
    .rank-name { font-size: 14px; font-weight: 700; color: #FFFFFF; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px; }
    .rank-handle { font-size: 12px; font-weight: 400; color: #9CA3AF; line-height: 1.2; }
    
    .rank-share { font-size: 13px; font-weight: 700; color: #10B981; min-width: 50px; text-align: right; margin-right: 10px; }
    .rank-followers { font-size: 13px; font-weight: 600; color: #E5E7EB; text-align: right; min-width: 70px; }
    
    .rank-category { font-size: 10px; color: #9CA3AF; background-color: #374151; padding: 2px 6px; border-radius: 8px; margin-right: 8px; display: none; }
    @media (min-width: 640px) { .rank-category { display: block; } .rank-name { max-width: 300px; } }
    
    h1, h2, h3 { font-family: 'sans-serif'; color: #FFFFFF !important; }
    .js-plotly-plot .plotly .main-svg { background-color: rgba(0,0,0,0) !important; }

    .js-plotly-plot .plotly .main-svg g.shapelayer path { transition: filter 0.2s ease; cursor: pointer; }
    .js-plotly-plot .plotly .main-svg g.shapelayer path:hover { filter: brightness(1.2) !important; opacity: 1 !important; }

    /* 방문자 카운터 스타일 */
    .visitor-box {
        background-color: #1C1F26;
        border: 1px solid #2D3035;
        border-radius: 12px;
        padding: 15px;
        margin-top: 20px;
        text-align: center;
    }
    .vis-label { font-size: 11px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px; }
    .vis-val { font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 5px; font-family
