# app.py 의 st.markdown style 부분 중 사이드바 관련 CSS만 아래로 교체

    /* 사이드바 메뉴 스타일 (알약 모양) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 2px; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child { display: none !important; }
    
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
        display: flex; width: 100%; padding: 6px 12px !important;
        border-radius: 8px !important; border: none !important;
        background-color: transparent; transition: all 0.2s ease; margin-bottom: 1px;
    }

    /* 기본 상태 텍스트 색상 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label div,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label span {
        color: #B0B3B8 !important; font-size: 14px; font-weight: 500;
    }

    /* 호버 상태 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover { background-color: #282A2C !important; }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover p,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover span,
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover div { 
        color: #FFFFFF !important; 
    }
    
    /* [선택된 메뉴] 스타일 (흰색 글씨 강제 적용 - 강력하게!) */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) { 
        background-color: #004A77 !important; 
    }
    
    /* 선택된 항목 내부의 모든 텍스트 요소 흰색 강제 */
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) * { 
        color: #FFFFFF !important; 
        font-weight: 700; 
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) p { 
        color: #FFFFFF !important; 
    }
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) div { 
        color: #FFFFFF !important; 
    }
