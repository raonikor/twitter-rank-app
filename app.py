import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import numpy as np
import html 
from datetime import datetime, timedelta, timezone

# [모듈 불러오기]
# 파일들이 같은 폴더에 있어야 합니다.
import market_logic 
import visitor_logic
import event_logic 
import twitter_logic
import payout_logic
import follower_logic
import project_logic # [필수] 프로젝트 맵 모듈

# 1. 페이지 설정
st.set_page_config(page_title="Raoni Map", layout="wide")

# 2. CSS 스타일
st.markdown("""
    <style>
    /* 전체 테마 */
    .stApp { background-color: #0F1115; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1E1F20; border-right: 1px solid #333; }
    
    /* ------------------------------------------------------- */
    /* [뉴스 티커] 상단 고정 스타일 */
    /* ------------------------------------------------------- */
    .ticker-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 50px;
        background-color: #16191E;
        border-bottom: 1px solid #2D3035;
        overflow: hidden;
        white-space: nowrap;
        padding: 12px 0;
        z-index: 999999;
        display: flex;
        align-items: center;
    }
    
    .ticker-wrapper {
        display: inline-block;
        padding-left: 100%;
        /* 속도 조절: 2500s (아주 천천히) */
        animation: ticker 2500s linear infinite; 
    }
    
    .ticker-item {
        display: inline-block;
        font-size: 14px;
        color: #E0E0E0;
        font-weight: 500;
        padding-right: 60px;
    }
    
    .ticker-highlight {
        color: #10B981; /* 이름 강조 (녹색) */
        font-weight: 700;
    }
    
    .ticker-handle {
        color: #9CA3AF; /* 핸들 (회색) */
        font-size: 12px;
        margin-right: 8px;
    }

    @keyframes ticker {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }

    /* 메인 컨텐츠 상단 여백 확보 (티커에 가려지지 않게) */
    .main .block-container {
        padding-top: 80px !important;
    }

    /* ------------------------------------------------------- */
    /* 사이드바 스타일 (세로형 알약 버튼) */
    /* ------------------------------------------------------- */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] { 
        display: flex; flex-direction: column !important; gap: 6px; 
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child { 
        display: none !important; 
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        display: flex; width: 100%; padding: 10px 16px !important;
        border-radius: 12px !important; border: 1px solid transparent !important;
        background-color: transparent; transition: all 0.2s ease; margin-bottom: 0px; align-items: center;
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label div,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label span {
        color: #9CA3AF !important; font-size: 14px; font-weight:
