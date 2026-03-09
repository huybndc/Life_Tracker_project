"""
=============================================================
File: ui_sections.py
Version: 0.6.0
Mục đích: Tầng Logic UI — các form nhập liệu.

THAY ĐỔI TRONG v0.6.0:
- simple_eval() hiển thị cảnh báo khi người dùng nhập sai
- Xoá dead CSS class (pillar-row, pillar-track, pillar-fill,
  score-hero, score-grade-badge, score-label — các class này
  được định nghĩa nhưng không dùng trong v0.5.x)
- Khoảng cách dùng CSS margin thay vì st.markdown("<br>")
- _safe_str() và _safe_in_list() giữ nguyên từ v0.5.1
=============================================================
"""

import streamlit as st
import re
from config import LEVELS, EXERCISE_TYPES, DAY_TYPES, THEME


# =============================================================
# PHẦN 1: HELPER — XỬ LÝ GIÁ TRỊ NaN AN TOÀN
# =============================================================

def _safe_str(value, default):
    """
    Trả về giá trị hợp lệ, hoặc default nếu value là NaN/None/rỗng.

    NaN (Not a Number) xuất hiện khi CSV có ô trống.
    Không thể dùng value == NaN vì NaN != NaN (đặc tính của IEEE 754).
    Dùng str(value) == "nan" để phát hiện.
    """
    if value is None or str(value).strip() in ("nan", ""):
        return default
    return value


def _safe_in_list(value, options: list, default):
    """
    Đảm bảo value tồn tại trong options trước khi gọi .index().

    list.index(value) crash với ValueError nếu value không có trong list.
    Hàm này kiểm tra trước → trả về default nếu không hợp lệ.
    """
    return value if value in options else default


# =============================================================
# PHẦN 2: TÍNH TOÁN SỐ HỌC AN TOÀN
# =============================================================

def simple_eval(expression: str) -> tuple:
    """
    Parse và tính giá trị của chuỗi toán học.

    THAY ĐỔI v0.6.0:
    Trả về tuple (result, error_message) thay vì chỉ float.
    Nếu thành công: (float_value, None)
    Nếu lỗi:       (0.0, "thông báo lỗi")
    → Caller có thể hiển thị cảnh báo cho người dùng.

    Bảo mật: regex whitelist chỉ cho phép [0-9 + - * / .]
    """
    try:
        cleaned = str(expression).replace(" ", "")
        safe    = re.sub(r'[^0-9+\-*/.]', '', cleaned)

        if not safe or safe in ("+", "-", "*", "/"):
            return 0.0, None  # Ô trống → không phải lỗi, chỉ là 0

        result = float(eval(safe))  # noqa: S307 — input đã được sanitize
        return result, None

    except ZeroDivisionError:
        return 0.0, "Không thể chia cho 0"
    except Exception:
        return 0.0, f"Không thể tính: '{expression}'"


# =============================================================
# PHẦN 3: FORM NHẬP LIỆU THỂ CHẤT
# =============================================================

def section_physical(last_entry=None, df=None):
    """
    Vẽ form nhập liệu Thể Chất: Sleep Hours, Sleep Quality,
    Exercise, Energy Level.

    Tham số:
        last_entry: pandas Series — dòng dữ liệu gần nhất (để điền sẵn)
        df:         DataFrame — toàn bộ dữ liệu (để hiện badge 7 ngày)

    Trả về:
        tuple: (sleep_hours, sleep_quality, exercise, energy)
    """
    st.markdown(
        f"<p style='font-family:serif; font-size:15px; font-weight:600;"
        f" color:{THEME['accent']}; margin:0 0 10px;'>🛌 &nbsp;Physical</p>",
        unsafe_allow_html=True,
    )

    if df is not None and not df.empty and len(df) >= 2:
        avg = df.tail(7)["sleep_hours"].mean()
        st.caption(f"7-day avg sleep · **{avg:.1f}h**")

    # Sleep Hours
    raw_sleep = _safe_str(
        last_entry["sleep_hours"] if (last_entry is not None and "sleep_hours" in last_entry) else None,
        default=7,
    )
    try:
        def_sleep = max(1, min(12, int(float(raw_sleep))))
    except (ValueError, TypeError):
        def_sleep = 7

    sleep_hours = st.select_slider("Sleep Hours", options=list(range(1, 13)), value=def_sleep)

    # Sleep Quality
    raw_q     = _safe_str(last_entry.get("sleep_quality") if last_entry is not None else None, LEVELS[2])
    def_q     = _safe_in_list(raw_q, LEVELS, LEVELS[2])
    sleep_quality = st.select_slider("Sleep Quality", options=LEVELS, value=def_q)

    # Exercise
    raw_exe   = _safe_str(last_entry.get("exercise") if last_entry is not None else None, EXERCISE_TYPES[0])
    def_exe   = _safe_in_list(raw_exe, EXERCISE_TYPES, EXERCISE_TYPES[0])
    exercise  = st.radio("Exercise", EXERCISE_TYPES, index=EXERCISE_TYPES.index(def_exe), horizontal=True)

    # Energy
    raw_nrg   = _safe_str(last_entry.get("energy") if last_entry is not None else None, LEVELS[2])
    def_nrg   = _safe_in_list(raw_nrg, LEVELS, LEVELS[2])
    energy    = st.select_slider("Energy Level", options=LEVELS, value=def_nrg)

    return sleep_hours, sleep_quality, exercise, energy


# =============================================================
# PHẦN 4: FORM NHẬP LIỆU NĂNG SUẤT
# =============================================================

def section_productivity(last_entry=None, df=None):
    """
    Vẽ form nhập liệu Năng Suất: Day Type, Study Hours, Focus Quality.

    Trả về:
        tuple: (day_type, study_hours, focus)
    """
    st.markdown(
        f"<p style='font-family:serif; font-size:15px; font-weight:600;"
        f" color:{THEME['accent']}; margin:0 0 10px;'>📚 &nbsp;Productivity</p>",
        unsafe_allow_html=True,
    )

    if df is not None and not df.empty and len(df) >= 2:
        total = df.tail(7)["study_hours"].sum()
        st.caption(f"7-day study total · **{total:.0f}h**")

    # Day Type
    raw_day  = _safe_str(last_entry.get("day_type") if last_entry is not None else None, DAY_TYPES[0])
    def_day  = _safe_in_list(raw_day, DAY_TYPES, DAY_TYPES[0])
    day_type = st.radio("Day Type", DAY_TYPES, index=DAY_TYPES.index(def_day), horizontal=True)

    # Study Hours
    raw_study = _safe_str(last_entry.get("study_hours") if last_entry is not None else None, 2)
    try:
        def_study = max(0, min(14, int(float(raw_study))))
    except (ValueError, TypeError):
        def_study = 2
    study_hours = st.select_slider("Study Hours", options=list(range(0, 15)), value=def_study)

    # Focus
    raw_foc = _safe_str(last_entry.get("focus") if last_entry is not None else None, LEVELS[2])
    def_foc = _safe_in_list(raw_foc, LEVELS, LEVELS[2])
    focus   = st.select_slider("Focus Quality", options=LEVELS, value=def_foc)

    return day_type, study_hours, focus


# =============================================================
# PHẦN 5: FORM NHẬP LIỆU TÀI CHÍNH & NHẬT KÝ
# =============================================================

def section_finance(last_entry=None, is_today=False):
    """
    Vẽ form Tài Chính (Spending, Income) và Nhật Ký tự do.

    THAY ĐỔI v0.6.0:
    - simple_eval() giờ trả về (value, error) — hiển thị cảnh báo
      ngay dưới ô nhập nếu người dùng nhập sai cú pháp

    Tham số:
        last_entry: pandas Series hoặc None
        is_today:   True nếu đang edit log hôm nay (điền lại giá trị cũ)

    Trả về:
        tuple: (spending, income, notes, spend_memo, income_memo)
    """
    st.markdown(
        f"<p style='font-family:serif; font-size:15px; font-weight:600;"
        f" color:{THEME['accent']}; margin:0 0 10px;'>🌿 &nbsp;Finance / Notes</p>",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)

    with col_a:
        raw_spend = last_entry["spending"] if (last_entry is not None and is_today) else None
        def_spend = str(_safe_str(raw_spend, default=0))
        spend_raw = st.text_input("Spending  (e.g. 5000+3*1200)", value=def_spend)

        # v0.6.0: nhận cả lỗi và hiển thị cho người dùng
        spending, spend_err = simple_eval(spend_raw)
        if spend_err:
            st.warning(f"⚠ {spend_err}")
        else:
            st.caption(f"→ **{spending:,.0f} ₩**")

        raw_sm     = last_entry.get("spend_memo") if (last_entry is not None and is_today) else None
        def_sm     = str(_safe_str(raw_sm, default=""))
        spend_memo = st.text_input("Spending Note", value=def_sm,
                                   placeholder="Coffee? Rent?", key="sm")

    with col_b:
        raw_inc   = last_entry["income"] if (last_entry is not None and is_today) else None
        def_inc   = str(_safe_str(raw_inc, default=0))
        income_raw = st.text_input("Income  (e.g. 100000-5000)", value=def_inc)

        income, income_err = simple_eval(income_raw)
        if income_err:
            st.warning(f"⚠ {income_err}")
        else:
            st.caption(f"→ **{income:,.0f} ₩**")

        raw_im      = last_entry.get("income_memo") if (last_entry is not None and is_today) else None
        def_im      = str(_safe_str(raw_im, default=""))
        income_memo = st.text_input("Income Note", value=def_im,
                                    placeholder="Salary? Gift?", key="im")

    # Số dư ròng
    net   = income - spending
    color = THEME["success"] if net >= 0 else THEME["danger"]
    sign  = "+" if net >= 0 else ""
    st.markdown(
        f"<p style='text-align:center; color:{THEME['text_muted']};"
        f" margin:8px 0 4px; font-size:13px;'>"
        f"Today's net &nbsp;"
        f"<span style='color:{color}; font-weight:700; font-size:15px;'>"
        f"{sign}{net:,.0f} ₩</span></p>",
        unsafe_allow_html=True,
    )

    st.divider()

    raw_notes = last_entry.get("notes") if (last_entry is not None and is_today) else None
    def_notes = str(_safe_str(raw_notes, default=""))
    notes = st.text_area(
        "Daily Journal",
        value=def_notes,
        height=240,
        placeholder="Hôm nay bạn cảm thấy thế nào? Học được gì? Biết ơn điều gì?",
    )

    return spending, income, notes, spend_memo, income_memo
