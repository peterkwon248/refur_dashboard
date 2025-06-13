import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import re
import json

# 🔐 서비스 계정 키는 Streamlit Secrets에서 가져오기
service_account_info = st.secrets["gcp_service_account"]
credentials = Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
gc = gspread.authorize(credentials)

# 📌 구글 시트 정보 (리퍼 판매현황)
SPREADSHEET_ID = "1O1eIiuYXjpTBclv-4_RYKvmJELglr7cGUfQ18eWUeVE"
WORKSHEET_NAME = "배송및 정산대기중"  # ✅ 시트 이름 정확히 반영

# 📥 데이터 불러오기
worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
records = worksheet.get_all_records()
df = pd.DataFrame(records)

# 💰 숫자(정산 금액) 정제 함수
def clean_price(value):
    if isinstance(value, str):
        return int(re.sub(r"[^\d]", "", value)) if re.sub(r"[^\d]", "", value) else 0
    return int(value) if isinstance(value, (int, float)) else 0

# 💰 정산 금액 컬럼 정리
if "정산 금액" in df.columns:
    df["정산 금액"] = df["정산 금액"].apply(clean_price)

# ✅ Streamlit UI 시작
st.set_page_config(page_title="📦 Refur Dashboard", layout="wide")
st.title("📦 리퍼제품 판매 대시보드")

# 🔍 거래 상태 필터
if "거래 상태" in df.columns:
    unique_status = df["거래 상태"].dropna().unique().tolist()
    selected_status = st.sidebar.multiselect("📌 거래 상태", unique_status, default=unique_status)
    df = df[df["거래 상태"].isin(selected_status)]

# 📊 통계 요약
st.subheader("📊 통계 요약")
col1, col2 = st.columns(2)
col1.metric("총 거래 수", len(df))
col2.metric("총 정산 금액", f"{df['정산 금액'].sum():,} 원" if "정산 금액" in df.columns else "N/A")

# 📈 거래 상태별 비율
if "거래 상태" in df.columns:
    st.subheader("📈 거래 상태 비율")
    status_counts = df["거래 상태"].value_counts().reset_index()
    status_counts.columns = ["거래 상태", "건수"]
    fig = px.pie(status_counts, names="거래 상태", values="건수", title="거래 상태 비율")
    st.plotly_chart(fig, use_container_width=True)

# 📋 전체 거래 내역
st.subheader("📋 전체 거래 내역")
st.dataframe(df, use_container_width=True)
