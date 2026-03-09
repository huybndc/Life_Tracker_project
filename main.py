"""
Main Entry Point: life_tracker.py
Architecture: Modular UI Component System
Goal: Clean State Management & Data Persistence
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from modules.dataset import load_dataset, save_dataset
from modules.ui_sections import section_physical, section_productivity, section_finance

# =========================================================
# APP CONFIGURATION
# WHY: 'layout=wide' provides the necessary horizontal space 
#      for side-by-side technical logging columns.
# =========================================================
st.set_page_config(page_title="Personal Life Tracker", layout="wide")

# =========================================================
# THEME: Visual Hierarchy
# WHY: Custom CSS cards (.section-card) group related logic.
#      It mimics the structure of a professional Dashboard.
# =========================================================
st.markdown("""
    <style>
    .section-card { background-color: #f7f9fc; padding: 20px; border-radius: 15px; border: 1px solid #e6e9ef; margin-bottom: 20px; }
    .stButton button { background-color: #4f6df5; color: white; font-weight: 600; border-radius: 10px; height: 3.5em; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# TIME LOGIC: KST Alignment
# HOW: Force Asia/Seoul timezone using pytz.
# WHY: Ensures that "Today" in the app always matches the 
#      user's local Korean date, regardless of server location.
# =========================================================
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.now(kst)
date_display = now_kst.strftime("%Y-%m-%d")
time_display = now_kst.strftime("%H:%M")
today = now_kst.replace(tzinfo=None)

# =========================================================
# DATA STATE: Persistence Check
# WHAT: Detects if a log already exists for the current date.
# HOW: Calendar day comparison (dt.date).
# WHY: This creates a 'Smart UI' that switches between 
#      'Insert Mode' and 'Update Mode' automatically.
# =========================================================
df = load_dataset()
is_today = False
last_entry = None

if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    last_entry = df.iloc[-1]
    if last_entry['date'].date() == today.date():
        is_today = True

# UI: Header & Time
st.title("Personal Life Tracker")
st.markdown(f"<div style='text-align:center; font-size:24px; font-weight:700;'>{date_display} <span style='color:#4f6df5'>{time_display}</span></div>", unsafe_allow_html=True)

# UI: Status Badge
status_color = "#d1fae5" if is_today else "#fee2e2"
st.markdown(f"<div style='text-align:center; margin-bottom:30px;'><span style='background-color:{status_color}; padding:5px 15px; border-radius:20px; font-weight:600;'>{'🟢 LOGGED' if is_today else '🔴 NOT LOGGED'}</span></div>", unsafe_allow_html=True)

# =========================================================
# UI: Core Input Grid
# HOW: We unpack returned values from ui_sections into local variables.
# =========================================================
st.header("Daily Log")
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    sleep_h, sleep_q, ex, nrg = section_physical(last_entry)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    d_type, s_h, foc = section_productivity(last_entry)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section-card'>", unsafe_allow_html=True)
# WHAT: Receives the 5 Finance/Journal variables
spend, inc, log, s_memo, i_memo = section_finance(last_entry, is_today)
st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# SAVE LOGIC: CRUD (Create, Update, Delete)
# HOW: 
#   1. Filter out today's row if it exists (Delete old state).
#   2. Concat new row (Create new state).
# WHY: Maintaining a 'Clean Dataset' where Date is the Unique Key.
# =========================================================
_, save_col, _ = st.columns([1,1,1])
with save_col:
    btn_label = "Update Today's Log" if is_today else "Save Daily Log"
    if st.button(btn_label):
        new_row = pd.DataFrame([{
            "date": today, "day_type": d_type,
            "sleep_hours": sleep_h, "sleep_quality": sleep_q,
            "exercise": ex, "energy": nrg,
            "study_hours": s_h, "focus": foc,
            "spending": spend, "income": inc, "notes": log,
            "spend_memo": s_memo, "income_memo": i_memo
        }])
        
        if not df.empty:
            df = df[df["date"].dt.date != today.date()]

        df = pd.concat([df, new_row], ignore_index=True)
        save_dataset(df)
        st.success(f"System Synchronized at {time_display} ✔")
        st.rerun()

# =========================================================
# DASHBOARD
# WHY: Providing 'Immediate Feedback' through visualization.
# =========================================================
st.divider()
if not df.empty:
    tab1, tab2 = st.tabs(["📈 Insights", "📁 Database"])
    with tab1:
        st.subheader("Study Continuity")
        st.line_chart(df.tail(7).set_index("date")["study_hours"])
    with tab2:
        st.dataframe(df.tail(10), use_container_width=True)