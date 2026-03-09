"""
Module: ui_sections.py
Version: 0.3.17
Goal: Logic Decoupling (Tách biệt logic giao diện và xử lý dữ liệu)
"""

import streamlit as st
import re
from config import LEVELS, EXERCISE_TYPES, DAY_TYPES

# =========================================================
# ⭐ LOGIC: Arithmetic String Evaluator
# WHAT: A safe parser for mathematical strings (e.g., "5000+2000").
# HOW: 
#   1. Clean whitespaces.
#   2. Use Regex to strip EVERYTHING except digits and (+, -).
#   3. Eval the sanitized string.
# WHY: Minimizes "Calculation Friction". Users hate switching apps 
#      to a calculator. This allows "Thinking in transactions".
# =========================================================
def simple_eval(expression):
    try:
        expr_str = str(expression).replace(" ", "")
        # Security: Regex acts as a 'Firewall' against code injection
        clean_expr = re.sub(r'[^0-9+\-]', '', expr_str)
        if not clean_expr: return 0.0
        return float(eval(clean_expr))
    except Exception:
        return 0.0

# =========================================================
# SECTION: Physical Tracking
# WHAT: UI for Sleep and Body Metrics.
# HOW: Uses select_sliders to map ordinal data (LEVELS).
# WHY: Sliders provide "Visual Constraints". They prevent 
#      invalid inputs and reduce cognitive load compared 
#      to typing numbers.
# =========================================================
def section_physical(last_entry=None):
    st.subheader("Physical")
    
    # Logic: Fallback to baseline (7h) if last_entry is missing
    def_sleep = 7
    if last_entry is not None and 'sleep_hours' in last_entry:
        def_sleep = int(last_entry['sleep_hours'])
        
    sleep_hours = st.select_slider("Sleep Hours", options=list(range(1, 13)), value=def_sleep)

    # Why .get(): Essential for 'Forward Compatibility' when adding new columns
    def_q = last_entry.get('sleep_quality', LEVELS[2]) if last_entry is not None else LEVELS[2]
    sleep_quality = st.select_slider("Sleep Quality", options=LEVELS, value=def_q)

    def_exe = last_entry.get('exercise', EXERCISE_TYPES[0]) if last_entry is not None else EXERCISE_TYPES[0]
    exercise = st.radio("Exercise", EXERCISE_TYPES, index=EXERCISE_TYPES.index(def_exe), horizontal=True)

    def_nrg = last_entry.get('energy', LEVELS[2]) if last_entry is not None else LEVELS[2]
    energy = st.select_slider("Energy Level", options=LEVELS, value=def_nrg)

    return sleep_hours, sleep_quality, exercise, energy

# =========================================================
# SECTION: Productivity Tracking
# WHAT: Cognitive output and study metrics.
# HOW: Synchronizes index of radio buttons with config.py
# WHY: 'Day Type' affects how we interpret 'Study Hours'. 
#      Logging them together creates a 'Contextual Data Point'.
# =========================================================
def section_productivity(last_entry=None):
    st.subheader("Productivity")

    def_day = last_entry.get('day_type', DAY_TYPES[0]) if last_entry is not None else DAY_TYPES[0]
    day_type = st.radio("Day Type", DAY_TYPES, index=DAY_TYPES.index(def_day), horizontal=True)

    def_study = int(last_entry.get('study_hours', 2)) if last_entry is not None else 2
    study_hours = st.select_slider("Study Hours", options=list(range(0, 15)), value=def_study)

    def_foc = last_entry.get('focus', LEVELS[2]) if last_entry is not None else LEVELS[2]
    focus = st.select_slider("Focus Quality", options=LEVELS, value=def_foc)

    return day_type, study_hours, focus

# =========================================================
# SECTION: Finance & Journal
# WHAT: Quantitative (Finance) + Qualitative (Journal) data.
# HOW: Uses a 2-column layout for finance to maximize vertical space.
# WHY: Separating 'Spending' and 'Memo' allows for future 
#      Categorization Analysis (e.g., "Why did I spend this?").
# =========================================================
def section_finance(last_entry=None, is_today=False):
    st.subheader("Finance / Notes")

    col_a, col_b = st.columns(2)
    with col_a:
        # Smart Recovery: Only restore spending/income if we are EDITING today's log.
        # Otherwise, start with "0" for a new day.
        def_spend = str(last_entry['spending']) if (last_entry is not None and is_today) else "0"
        spend_raw = st.text_input("Spending (e.g. 50+20)", value=def_spend)
        spending = simple_eval(spend_raw)
        st.caption(f"Parsed Value: **{spending:,.0f}**")
        
        def_sm = last_entry.get('spend_memo', "") if (last_entry is not None and is_today) else ""
        spend_memo = st.text_input("Spending Note", value=def_sm, placeholder="Coffee? Rent?", key="sm")

    with col_b:
        def_inc = str(last_entry['income']) if (last_entry is not None and is_today) else "0"
        income_raw = st.text_input("Income (e.g. 100-20)", value=def_inc)
        income = simple_eval(income_raw)
        st.caption(f"Parsed Value: **{income:,.0f}**")
        
        def_im = last_entry.get('income_memo', "") if (last_entry is not None and is_today) else ""
        income_memo = st.text_input("Income Note", value=def_im, placeholder="Salary? Gift?", key="im")

    st.divider()
    # Why height=280: Better for 'Social Commentary' / Essay-style logging.
    def_notes = last_entry.get('notes', "") if (last_entry is not None and is_today) else ""
    notes = st.text_area("Daily Journal", value=def_notes, height=280, placeholder="Logic insights...")

    return spending, income, notes, spend_memo, income_memo