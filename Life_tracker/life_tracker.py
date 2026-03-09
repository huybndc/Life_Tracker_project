"""
=============================================================
File: life_tracker.py
Version: 0.6.0
Mục đích: File chính — điểm vào duy nhất của app.

THAY ĐỔI TRONG v0.6.0:
- Tách toàn bộ dashboard ra modules/dashboard.py
  → File này giảm từ 600+ dòng xuống ~280 dòng
- Thêm spinner khi bấm Save (người dùng biết app đang xử lý)
- Thêm gợi ý cải thiện trụ cột yếu trong Life Score card
- Tất cả import ở đầu file (fix PEP 8)
- Dùng PILLAR_COLORS và SCORE_MESSAGES từ config (không hardcode)
- Thêm nút Delete Today's Log trong sidebar

CẤU TRÚC FILE (top → bottom):
    1. Import
    2. Cấu hình trang + CSS
    3. Thời gian KST
    4. Load dữ liệu
    5. Header
    6. Form nhập liệu
    7. Life Score card (realtime)
    8. Nút Save + Delete
    9. Dashboard (gọi render_dashboard)
=============================================================
"""

# =============================================================
# IMPORT — TẤT CẢ Ở ĐẦU FILE (PEP 8)
# =============================================================

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

from modules.dataset import (
    load_dataset, save_dataset,
    compute_life_score, get_grade,
    get_pillar_scores, get_score_message,
    get_streak, get_weekly_summary,
)
from modules.ui_sections import (
    section_physical, section_productivity, section_finance,
)
from modules.dashboard import render_dashboard

# ── FIX: GRADE_THRESHOLDS import ở đây, không nằm trong tab ──
from config import (
    THEME, LEVEL_SCORES,
    PILLAR_COLORS, PILLAR_TIPS,
    GRADE_THRESHOLDS,
    SLEEP_OPTIMAL_HOURS, FINANCE_REFERENCE,
)


# =============================================================
# PHẦN 1: CẤU HÌNH TRANG
# =============================================================

# Phải là lệnh Streamlit đầu tiên được gọi
st.set_page_config(
    page_title="Life Tracker",
    layout="wide",
    page_icon="🌿",
)


# =============================================================
# PHẦN 2: CSS TOÀN CỤC
# =============================================================
# Lưu ý: Đã XOÁ các class CSS không dùng từ v0.5.x:
#   .pillar-row, .pillar-track, .pillar-fill  → dùng inline style
#   .score-hero, .score-grade-badge           → dùng inline style
#   .card-warm                                → không dùng đến
# Chỉ giữ lại những class THỰC SỰ được dùng trong HTML bên dưới.

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;600;700&family=Source+Sans+3:wght@300;400;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Source Sans 3', sans-serif;
    background-color: {THEME['bg']};
    color: {THEME['text']};
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{
    padding-top: 2.2rem;
    padding-bottom: 3rem;
    max-width: 1160px;
}}
h1, h2, h3 {{
    font-family: 'Lora', serif;
    color: {THEME['text']};
}}

/* ── Card ── */
.card {{
    background: {THEME['surface']};
    border: 1px solid {THEME['border']};
    border-radius: 16px;
    padding: 24px 26px;
    margin-bottom: 16px;
}}

/* ── KPI (Dashboard) ── */
.kpi {{
    background: {THEME['surface']};
    border: 1px solid {THEME['border']};
    border-radius: 12px;
    padding: 14px 12px;
    text-align: center;
    margin-bottom: 4px;
}}
.kpi-val {{
    font-family: 'Lora', serif;
    font-size: 22px;
    font-weight: 700;
    line-height: 1.1;
}}
.kpi-lbl {{
    font-size: 10px;
    color: {THEME['text_muted']};
    text-transform: uppercase;
    letter-spacing: .07em;
    margin-top: 4px;
}}

/* ── Tip card (gợi ý cải thiện) ── */
.tip-card {{
    background: {THEME['highlight']};
    border-left: 3px solid {THEME['warning']};
    border-radius: 0 8px 8px 0;
    padding: 8px 12px;
    margin: 5px 0;
    font-size: 12px;
    color: {THEME['text_muted']};
}}

hr {{ border-color: {THEME['border']}; margin: 20px 0; }}

/* ── Streamlit overrides ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    background-color: {THEME['highlight']} !important;
    border-color: {THEME['border']} !important;
    color: {THEME['text']} !important;
    border-radius: 10px !important;
    font-family: 'Source Sans 3', sans-serif !important;
}}
.stButton > button {{
    background: linear-gradient(135deg, {THEME['accent']} 0%, {THEME['accent3']} 100%) !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-family: 'Source Sans 3', sans-serif !important;
    border-radius: 12px !important;
    border: none !important;
    height: 3.2em;
    width: 100%;
    letter-spacing: .03em;
    transition: opacity .15s;
}}
.stButton > button:hover {{ opacity: 0.88; }}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Source Sans 3', sans-serif;
    font-size: 12px;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: {THEME['text_muted']};
}}
.stTabs [aria-selected="true"] {{
    color: {THEME['accent']} !important;
    border-bottom-color: {THEME['accent']} !important;
}}
</style>
""", unsafe_allow_html=True)


# =============================================================
# PHẦN 3: THỜI GIAN — KST
# =============================================================
# Server Streamlit Cloud chạy ở UTC → cần ép múi giờ Seoul

kst      = pytz.timezone("Asia/Seoul")
now_kst  = datetime.now(kst)
date_disp = now_kst.strftime("%B %d, %Y")   # "March 09, 2026"
time_disp = now_kst.strftime("%H:%M")        # "20:04"
dow_disp  = now_kst.strftime("%A")           # "Monday"
today     = now_kst.replace(tzinfo=None)     # Bỏ timezone info để so sánh với CSV


# =============================================================
# PHẦN 4: LOAD DỮ LIỆU
# =============================================================

df = load_dataset()

is_today   = False
last_entry = None

if not df.empty:
    df["date"] = pd.to_datetime(df["date"])
    last_entry = df.iloc[-1]
    if last_entry["date"].date() == today.date():
        is_today = True

streak  = get_streak(df)
summary = get_weekly_summary(df)


# =============================================================
# PHẦN 5: HEADER
# =============================================================

left, right = st.columns([3, 1])

with left:
    st.markdown(
        f"<div style='margin-bottom:4px;'>"
        f"<span style='font-size:12px; color:{THEME['text_muted']};"
        f" letter-spacing:.08em; text-transform:uppercase;'>{dow_disp.upper()}</span><br>"
        f"<span style='font-family:Lora,serif; font-size:2.2rem; font-weight:700;"
        f" color:{THEME['accent']};'>Life Tracker</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='font-size:15px; color:{THEME['text_muted']}; margin:2px 0 0;'>"
        f"{date_disp} &nbsp;·&nbsp; {time_disp}</p>",
        unsafe_allow_html=True,
    )

with right:
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # Badge trạng thái
    if is_today:
        st.markdown(
            f"<div style='text-align:right;'><span style='background:#ddeedd;"
            f" color:{THEME['success']}; border:1px solid {THEME['success']}50;"
            f" padding:5px 14px; border-radius:20px; font-size:12px; font-weight:600;'>"
            f"✦ &nbsp;Logged Today</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='text-align:right;'><span style='background:#f5dede;"
            f" color:{THEME['danger']}; border:1px solid {THEME['danger']}50;"
            f" padding:5px 14px; border-radius:20px; font-size:12px; font-weight:600;'>"
            f"○ &nbsp;Not Logged</span></div>",
            unsafe_allow_html=True,
        )

    # Streak
    streak_color = THEME["warning"] if streak > 0 else THEME["text_muted"]
    streak_text  = f"🔥 {streak}-day streak" if streak > 0 else "Start your streak today"
    st.markdown(
        f"<p style='text-align:right; font-size:13px; color:{streak_color};"
        f" margin-top:8px;'><strong>{streak_text}</strong></p>",
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)


# =============================================================
# PHẦN 6: FORM NHẬP LIỆU
# =============================================================

st.markdown(
    f"<h3 style='font-family:Lora,serif; margin-bottom:16px;'>Today's Log</h3>",
    unsafe_allow_html=True,
)

col_phys, col_prod = st.columns(2)

with col_phys:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    sleep_h, sleep_q, ex, nrg = section_physical(last_entry, df=df)
    st.markdown("</div>", unsafe_allow_html=True)

with col_prod:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    d_type, s_h, foc = section_productivity(last_entry, df=df)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
spend, inc, log_notes, s_memo, i_memo = section_finance(last_entry, is_today)
st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# PHẦN 7: LIFE SCORE CARD — REALTIME
# =============================================================
# Tính từ giá trị slider hiện tại → cập nhật ngay khi kéo

live_score          = compute_life_score(sleep_h, sleep_q, ex, nrg, s_h, foc, spend, inc)
live_grade, g_color = get_grade(live_score)
pillars             = get_pillar_scores(sleep_h, sleep_q, ex, nrg, s_h, foc, spend, inc)

# Tính thông số SVG ring gauge
# Kỹ thuật: stroke-dasharray = "đoạn_tô đoạn_trống" trên circle
r    = 52
circ = 2 * 3.14159 * r
dash = (live_score / 100) * circ
gap  = circ - dash

# Mở card
st.markdown(
    f"<div style='background:{THEME['surface']}; border:1px solid {THEME['border']};"
    f" border-radius:16px; padding:26px; margin-bottom:16px;'>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='font-family:Lora,serif; font-size:15px; font-weight:600;"
    f" color:{THEME['accent']}; margin:0 0 18px;'>✦ &nbsp;Life Score</p>",
    unsafe_allow_html=True,
)

ring_col, pillar_col = st.columns([1, 2])

with ring_col:
    # SVG Ring Gauge
    st.markdown(
        f'<div style="text-align:center; padding:8px 0;">'
        f'<svg width="130" height="130" viewBox="0 0 130 130">'
        f'<circle cx="65" cy="65" r="{r}" fill="none"'
        f' stroke="{THEME["surface2"]}" stroke-width="11"/>'
        f'<circle cx="65" cy="65" r="{r}" fill="none"'
        f' stroke="{THEME["accent"]}" stroke-width="11"'
        f' stroke-dasharray="{dash:.1f} {gap:.1f}"'
        f' stroke-linecap="round" transform="rotate(-90 65 65)"/>'
        f'<text x="65" y="62" text-anchor="middle"'
        f' font-family="serif" font-size="28" font-weight="700"'
        f' fill="{THEME["text"]}">{live_score:.0f}</text>'
        f'<text x="65" y="78" text-anchor="middle"'
        f' font-family="sans-serif" font-size="10"'
        f' fill="{THEME["text_muted"]}">OUT OF 100</text>'
        f'</svg>'
        f'<div style="font-family:serif; font-size:44px; font-weight:700;'
        f' color:{g_color}; line-height:1; margin-top:4px;">{live_grade}</div>'
        f'<div style="font-size:11px; color:{THEME["text_muted"]};'
        f' letter-spacing:.08em; text-transform:uppercase; margin-top:2px;">grade</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

with pillar_col:
    # Thông điệp — đọc từ config qua get_score_message()
    st.markdown(
        f"<p style='font-size:13px; color:{THEME['text_muted']};"
        f" margin:4px 0 14px; font-style:italic;'>"
        f"\"{get_score_message(live_score)}\"</p>",
        unsafe_allow_html=True,
    )

    # Progress bars — màu đọc từ PILLAR_COLORS trong config
    for name, val in pillars.items():
        color = PILLAR_COLORS.get(name, THEME["accent"])
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:10px; margin:7px 0;">'
            f'<span style="width:68px; font-size:12px; color:{THEME["text_muted"]};">{name}</span>'
            f'<div style="flex:1; background:{THEME["surface2"]}; border-radius:6px; height:9px; overflow:hidden;">'
            f'<div style="width:{val:.0f}%; background:{color}; height:9px; border-radius:6px;"></div>'
            f'</div>'
            f'<span style="width:36px; text-align:right; font-size:12px;'
            f' color:{THEME["text_muted"]};">{val:.0f}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── TÍNH NĂNG MỚI v0.6.0: Gợi ý cải thiện trụ cột yếu ──
    # Ngưỡng 40 điểm: trụ cột nào dưới 40 được coi là "yếu"
    # Hiển thị tối đa 2 gợi ý để không làm rối giao diện
    WEAK_THRESHOLD = 40
    weak_pillars = [(name, val) for name, val in pillars.items() if val < WEAK_THRESHOLD]

    if weak_pillars:
        st.markdown(
            f"<p style='font-size:11px; color:{THEME['warning']}; margin:14px 0 6px;"
            f" letter-spacing:.05em; text-transform:uppercase;'>💡 Gợi ý cải thiện</p>",
            unsafe_allow_html=True,
        )
        for name, _ in weak_pillars[:2]:   # Tối đa 2 gợi ý
            tip = PILLAR_TIPS.get(name, "")
            if tip:
                st.markdown(
                    f"<div class='tip-card'><strong>{name}:</strong> {tip}</div>",
                    unsafe_allow_html=True,
                )

# Đóng card
st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# PHẦN 8: NÚT SAVE + DELETE
# =============================================================

save_col, del_col = st.columns([2, 1])

with save_col:
    label = "↑ Update Today's Log" if is_today else "✦ Save Today's Log"

    if st.button(label, use_container_width=True):
        # Spinner: hiển thị "Đang lưu..." trong khi xử lý
        # → Người dùng không nghĩ app bị đơ
        with st.spinner("Đang lưu..."):
            final_score = compute_life_score(sleep_h, sleep_q, ex, nrg, s_h, foc, spend, inc)
            new_row     = pd.DataFrame([{
                "date":          today,
                "day_type":      d_type,
                "sleep_hours":   sleep_h,
                "sleep_quality": sleep_q,
                "exercise":      ex,
                "energy":        nrg,
                "study_hours":   s_h,
                "focus":         foc,
                "spending":      spend,
                "income":        inc,
                "spend_memo":    s_memo,
                "income_memo":   i_memo,
                "notes":         log_notes,
                "life_score":    final_score,
            }])

            # Xoá dòng hôm nay nếu đã tồn tại (tránh duplicate)
            if not df.empty:
                df_save = df[df["date"].dt.date != today.date()]
            else:
                df_save = df

            df_save = pd.concat([df_save, new_row], ignore_index=True)

            # save_dataset() dùng atomic write (ghi .tmp → rename)
            save_dataset(df_save)

        final_grade, _ = get_grade(final_score)
        st.success(
            f"✦ Đã lưu · Life Score: **{final_score}** · Xếp hạng: **{final_grade}** · {time_disp}"
        )
        st.rerun()

with del_col:
    # Nút xoá — chỉ hiển thị khi hôm nay đã có log
    if is_today:
        if st.button("🗑 Xoá log hôm nay", use_container_width=True):
            # Xác nhận trước khi xoá — dùng session_state để lưu trạng thái
            # st.session_state: dict đặc biệt của Streamlit, tồn tại qua re-run
            st.session_state["confirm_delete"] = True

# Hiển thị xác nhận xoá (nếu người dùng vừa bấm nút xoá)
if st.session_state.get("confirm_delete"):
    st.warning("⚠ Bạn có chắc muốn xoá log hôm nay không? Không thể hoàn tác.")
    yes_col, no_col = st.columns(2)
    with yes_col:
        if st.button("✓ Xác nhận xoá", use_container_width=True):
            df_del = df[df["date"].dt.date != today.date()]
            save_dataset(df_del)
            st.session_state["confirm_delete"] = False
            st.success("Đã xoá log hôm nay.")
            st.rerun()
    with no_col:
        if st.button("✗ Huỷ", use_container_width=True):
            st.session_state["confirm_delete"] = False
            st.rerun()


# =============================================================
# PHẦN 9: DASHBOARD
# =============================================================
# Toàn bộ dashboard được tách sang modules/dashboard.py
# life_tracker.py chỉ cần gọi 1 hàm

if not df.empty:
    render_dashboard(df, summary)
else:
    # Empty state khi chưa có dữ liệu nào
    st.markdown(
        f"<div style='text-align:center; padding:60px 20px; color:{THEME['text_muted']};'>"
        f"<div style='font-size:42px; margin-bottom:12px;'>🌿</div>"
        f"<div style='font-family:Lora,serif; font-size:18px; color:{THEME['accent']};'>"
        f"Hành trình của bạn bắt đầu từ đây.</div>"
        f"<div style='font-size:14px; margin-top:6px;'>"
        f"Điền form bên trên và bấm Save để bắt đầu theo dõi.</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
