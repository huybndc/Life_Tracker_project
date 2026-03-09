"""
=============================================================
File: modules/dashboard.py
Version: 0.6.0
Mục đích: Tầng Dashboard — tách toàn bộ phần biểu đồ và
          thống kê ra khỏi life_tracker.py.

TẠI SAO TÁCH FILE NÀY?
- life_tracker.py v0.5.x có 600+ dòng, làm quá nhiều việc.
- Tách dashboard ra → mỗi file có 1 trách nhiệm rõ ràng.
- Nguyên tắc SRP (Single Responsibility Principle):
  life_tracker.py = form nhập liệu + save
  dashboard.py    = hiển thị dữ liệu lịch sử

CÁC HÀM:
    render_dashboard(df, summary) → vẽ toàn bộ 4-tab dashboard
    _tab_life_score(df)           → tab Life Score history
    _tab_trends(df)               → tab Trends 14 ngày
    _tab_week(summary)            → tab This Week
    _tab_database(df)             → tab Database raw
=============================================================
"""

import io
import pandas as pd
import streamlit as st

# ── FIX v0.6.0: import ở đầu file, không nằm trong hàm ──
from config import THEME, LEVEL_SCORES, GRADE_THRESHOLDS, PILLAR_TIPS
from modules.dataset import get_grade


# =============================================================
# HELPER — KPI CARD
# =============================================================

def _kpi(col, val: str, lbl: str, color: str) -> None:
    """
    Vẽ một KPI card vào cột Streamlit cho sẵn.

    Được tách thành hàm riêng vì pattern này lặp lại nhiều lần
    trong cả tab_week lẫn tab_score.

    Tham số:
        col:   st.column context (từ st.columns())
        val:   giá trị lớn hiển thị (ví dụ: "67.3 (B)")
        lbl:   nhãn nhỏ bên dưới (ví dụ: "Latest Score")
        color: màu hex cho phần giá trị
    """
    col.markdown(
        f"<div class='kpi'>"
        f"<div class='kpi-val' style='color:{color};'>{val}</div>"
        f"<div class='kpi-lbl'>{lbl}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _section_label(text: str) -> None:
    """Vẽ nhãn nhỏ phía trên biểu đồ (uppercase, muted color)."""
    st.markdown(
        f"<p style='font-size:12px; color:{THEME['text_muted']};"
        f" letter-spacing:.06em; text-transform:uppercase;"
        f" margin:16px 0 4px;'>{text}</p>",
        unsafe_allow_html=True,
    )


def _empty_state(message: str) -> None:
    """Hiển thị thông báo khi chưa có đủ dữ liệu để vẽ biểu đồ."""
    st.markdown(
        f"<div style='text-align:center; padding:40px 20px;"
        f" color:{THEME['text_muted']}; background:{THEME['surface']};"
        f" border:1px dashed {THEME['border']}; border-radius:12px;"
        f" margin:16px 0;'>"
        f"<div style='font-size:28px; margin-bottom:8px;'>📊</div>"
        f"<div style='font-size:14px;'>{message}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# =============================================================
# TAB 1: LIFE SCORE HISTORY
# =============================================================

def _tab_life_score(df: pd.DataFrame) -> None:
    """
    Hiển thị:
    - 4 KPI cards: điểm gần nhất, trung bình 30 ngày, tốt nhất, tệ nhất
    - Line chart 30 ngày
    - Bar chart phân bố xếp hạng
    """
    # Lọc chỉ lấy các dòng đã có Life Score > 0
    score_df = df[df["life_score"] > 0].copy()

    # Empty state: chưa có dữ liệu nào
    if score_df.empty:
        _empty_state("Lưu log đầu tiên để bắt đầu theo dõi Life Score.")
        return

    # ── 4 KPI Cards ──
    best  = score_df["life_score"].max()
    worst = score_df["life_score"].min()
    avg   = score_df["life_score"].mean()
    last  = score_df["life_score"].iloc[-1]

    best_g, bc = get_grade(best)
    last_g, lc = get_grade(last)

    k1, k2, k3, k4 = st.columns(4)
    _kpi(k1, f"{last:.0f} ({last_g})",  "Latest Score",   lc)
    _kpi(k2, f"{avg:.1f}",              "30-day Average", THEME["accent"])
    _kpi(k3, f"{best:.0f} ({best_g})",  "Personal Best",  bc)
    _kpi(k4, f"{worst:.0f}",            "Personal Worst", THEME["text_muted"])

    # ── Line Chart ──
    # Empty state khi chỉ có 1 điểm — biểu đồ đường 1 điểm trông xấu
    if len(score_df) < 2:
        _empty_state("Cần ít nhất 2 ngày để hiển thị biểu đồ xu hướng.")
    else:
        _section_label("Life Score · 30 ngày gần nhất")
        st.line_chart(
            score_df.tail(30).set_index("date")["life_score"],
            color=THEME["accent"],
        )

    # ── Grade Distribution ──
    _section_label("Phân bố xếp hạng · Toàn bộ")

    # Khởi tạo dict đếm với tất cả grade = 0 (đảm bảo grade không có dữ liệu vẫn hiện)
    grade_counts = {g: 0 for _, g, _ in reversed(GRADE_THRESHOLDS)}
    for s in score_df["life_score"]:
        g, _ = get_grade(s)
        grade_counts[g] = grade_counts.get(g, 0) + 1

    grade_df = pd.DataFrame({
        "Grade": list(grade_counts.keys()),
        "Days":  list(grade_counts.values()),
    }).set_index("Grade")
    st.bar_chart(grade_df, color=THEME["accent3"])


# =============================================================
# TAB 2: TRENDS — 14 NGÀY
# =============================================================

def _tab_trends(df: pd.DataFrame) -> None:
    """
    4 biểu đồ xu hướng 14 ngày: Study, Sleep, Energy, Finance.

    Empty state khi có < 2 dòng dữ liệu.
    """
    if len(df) < 2:
        _empty_state("Cần ít nhất 2 ngày để hiển thị xu hướng.")
        return

    # Chuẩn bị dữ liệu biểu đồ
    chart_df = df.tail(14).set_index("date").copy()

    # Chuyển energy (chuỗi) → số để vẽ được
    # fillna(3) = Medium khi có giá trị lạ
    chart_df["energy_num"] = chart_df["energy"].map(LEVEL_SCORES).fillna(3)
    chart_df["balance"]    = chart_df["income"] - chart_df["spending"]

    # Hàng 1: Study | Sleep
    r1, r2 = st.columns(2)
    with r1:
        _section_label("Study Hours · 14 ngày")
        st.line_chart(chart_df["study_hours"], color=THEME["purple"])
    with r2:
        _section_label("Sleep Hours · 14 ngày")
        st.line_chart(chart_df["sleep_hours"], color=THEME["accent"])

    # Hàng 2: Energy | Finance
    r3, r4 = st.columns(2)
    with r3:
        _section_label("Energy Level · 14 ngày")
        st.line_chart(chart_df["energy_num"], color=THEME["accent2"])
    with r4:
        _section_label("Finance Balance · 14 ngày")
        # bar_chart phù hợp hơn line_chart cho số dư: dễ thấy âm/dương
        st.bar_chart(chart_df["balance"], color=THEME["accent3"])


# =============================================================
# TAB 3: THIS WEEK
# =============================================================

def _tab_week(summary: dict) -> None:
    """
    Thống kê 7 ngày gần nhất.

    Tham số:
        summary: dict từ get_weekly_summary() trong dataset.py
                 {} nếu chưa có đủ dữ liệu
    """
    if not summary:
        _empty_state("Cần ít nhất 1 ngày dữ liệu để xem thống kê tuần.")
        return

    net       = summary["net_balance"]
    net_color = THEME["success"] if net >= 0 else THEME["danger"]
    sign      = "+" if net >= 0 else ""

    # Hàng 1: 4 chỉ số sức khoẻ / học tập
    cols = st.columns(4)
    _kpi(cols[0], f"{summary['avg_sleep']}h",     "Avg Sleep",     THEME["accent"])
    _kpi(cols[1], f"{summary['avg_study']}h",     "Avg Study",     THEME["purple"])
    _kpi(cols[2], f"{summary['avg_energy']}/5",   "Avg Energy",    THEME["accent2"])
    _kpi(cols[3], f"{summary['exercise_days']}d", "Exercise Days", THEME["warning"])

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    # Hàng 2: 3 chỉ số tài chính
    cols2 = st.columns(3)
    _kpi(cols2[0], f"{summary['total_spend']:,.0f}",  "Total Spend ₩",  THEME["danger"])
    _kpi(cols2[1], f"{summary['total_income']:,.0f}", "Total Income ₩", THEME["success"])
    _kpi(cols2[2], f"{sign}{net:,.0f}",               "Net Balance ₩",  net_color)

    # Weekly Life Score (nếu có)
    avg_score = summary.get("avg_score", 0)
    if avg_score > 0:
        avg_g, avg_c = get_grade(avg_score)
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='text-align:center; padding:16px;"
            f" background:{THEME['surface']}; border:1px solid {THEME['border']};"
            f" border-radius:12px;'>"
            f"<span style='font-size:13px; color:{THEME['text_muted']};'>"
            f"Weekly Average Life Score</span><br>"
            f"<span style='font-family:Lora,serif; font-size:36px;"
            f" font-weight:700; color:{avg_c};'>{avg_score:.0f}</span>"
            f"<span style='font-size:20px; color:{avg_c}; margin-left:8px;'>"
            f"({avg_g})</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


# =============================================================
# TAB 4: DATABASE + DOWNLOAD
# =============================================================

def _tab_database(df: pd.DataFrame) -> None:
    """
    Hiển thị bảng dữ liệu thô và nút Download CSV.

    TÍNH NĂNG MỚI v0.6.0: Nút Download
    - Người dùng có thể tải xuống toàn bộ dữ liệu để backup
      hoặc phân tích sâu hơn trong Excel / Google Sheets.
    - st.download_button(): tạo nút tải file trực tiếp từ browser.
    - io.StringIO(): tạo file CSV trong bộ nhớ RAM thay vì ghi ra đĩa.
      Điều này an toàn hơn và nhanh hơn.
    """
    if df.empty:
        _empty_state("Chưa có dữ liệu để hiển thị.")
        return

    # Chuẩn bị bản sao để hiển thị (không sửa df gốc)
    disp = df.tail(30).copy()
    disp["date"] = disp["date"].dt.strftime("%Y-%m-%d")

    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    # ── Nút Download ──
    # Tạo CSV trong bộ nhớ (không cần ghi ra file tạm)
    # StringIO(): như một file text ảo trong RAM
    buffer = io.StringIO()
    export_df = df.copy()
    export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d")
    export_df.to_csv(buffer, index=False)
    csv_bytes = buffer.getvalue().encode("utf-8")
    # encode("utf-8"): chuyển chuỗi → bytes vì download_button cần bytes

    col_dl, col_info = st.columns([1, 3])
    with col_dl:
        st.download_button(
            label="⬇ Download CSV",
            data=csv_bytes,
            file_name="life_log_export.csv",
            mime="text/csv",           # Loại file: text/csv
            use_container_width=True,
        )
    with col_info:
        st.caption(
            f"Toàn bộ **{len(df)} dòng** · Dùng để backup hoặc mở trong Excel / Google Sheets."
        )


# =============================================================
# TAB 5: HƯỚNG DẪN SỬ DỤNG
# =============================================================

def _tab_guide() -> None:
    """
    Hướng dẫn sử dụng app cho người mới.

    TÍNH NĂNG MỚI v0.6.0:
    Trước đây không có hướng dẫn → người mới không biết:
    - Điểm Life Score tính thế nào?
    - Xếp hạng S/A/B/C/D/F nghĩa là gì?
    - Các trụ cột có trọng số ra sao?
    """
    from config import LIFE_SCORE_WEIGHTS, GRADE_THRESHOLDS, FINANCE_REFERENCE

    st.markdown(
        f"<p style='color:{THEME['text_muted']}; font-size:14px; margin-bottom:20px;'>"
        f"Mọi thứ bạn cần biết để dùng Life Tracker hiệu quả.</p>",
        unsafe_allow_html=True,
    )

    # ── Cách dùng hàng ngày ──
    st.markdown(
        f"<h4 style='font-family:Lora,serif; color:{THEME['accent']};"
        f" margin:0 0 10px;'>📋 Cách dùng hàng ngày</h4>",
        unsafe_allow_html=True,
    )
    steps = [
        ("1. Điền form buổi tối", "Mỗi tối trước khi ngủ, điền các thông số của ngày hôm đó vào form bên trên."),
        ("2. Xem điểm realtime",  "Kéo thử các slider — Life Score card cập nhật ngay lập tức, không cần bấm Save."),
        ("3. Bấm Save",           "Bấm nút Save để lưu xuống file CSV trên máy bạn."),
        ("4. Theo dõi xu hướng",  "Sau 7 ngày, tab TRENDS và THIS WEEK sẽ có dữ liệu đáng đọc."),
    ]
    for title, desc in steps:
        st.markdown(
            f"<div style='background:{THEME['surface']}; border-left:3px solid {THEME['accent']};"
            f" padding:10px 14px; border-radius:0 8px 8px 0; margin-bottom:8px;'>"
            f"<strong style='color:{THEME['text']};'>{title}</strong>"
            f"<p style='color:{THEME['text_muted']}; font-size:13px; margin:2px 0 0;'>{desc}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # ── Công thức Life Score ──
    st.markdown(
        f"<h4 style='font-family:Lora,serif; color:{THEME['accent']};"
        f" margin:0 0 10px;'>⚖️ Công thức Life Score</h4>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{THEME['text_muted']}; font-size:13px; margin-bottom:12px;'>"
        f"Điểm Life Score (0–100) = tổng hợp 6 trụ cột, mỗi trụ cột có trọng số riêng:</p>",
        unsafe_allow_html=True,
    )

    pillar_descs = {
        "sleep":    ("🛌 Giấc ngủ",    "Kết hợp giờ ngủ (lý tưởng 7.5h) và chất lượng ngủ"),
        "energy":   ("⚡ Năng lượng",   "Mức năng lượng chủ quan trong ngày"),
        "exercise": ("🏃 Vận động",     "None=0, Walk=40, Light=60, Hard=100 điểm"),
        "study":    ("📚 Học tập",      "Tối đa khi học 10h, tuyến tính từ 0"),
        "focus":    ("🎯 Tập trung",    "Chất lượng tập trung khi làm việc/học"),
        "finance":  ("💰 Tài chính",    f"Trung tính tại net=0, tối đa khi net ≥ +{FINANCE_REFERENCE:,}₩"),
    }

    for key, (emoji_name, desc) in pillar_descs.items():
        weight_pct = int(LIFE_SCORE_WEIGHTS[key] * 100)
        bar_w      = weight_pct * 3   # Pixel chiều rộng thanh bar
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:8px;'>"
            f"<span style='width:130px; font-size:13px; color:{THEME['text']};'>{emoji_name}</span>"
            f"<div style='width:{bar_w}px; height:8px; background:{THEME['accent']};"
            f" border-radius:4px; opacity:0.8;'></div>"
            f"<span style='font-size:13px; font-weight:700; color:{THEME['accent']};'>{weight_pct}%</span>"
            f"<span style='font-size:12px; color:{THEME['text_muted']};'>— {desc}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # ── Xếp hạng ──
    st.markdown(
        f"<h4 style='font-family:Lora,serif; color:{THEME['accent']};"
        f" margin:0 0 10px;'>🏅 Ý nghĩa xếp hạng</h4>",
        unsafe_allow_html=True,
    )
    grade_descs = {
        "S": "≥ 90  — Ngày xuất sắc. Mọi trụ cột đều mạnh.",
        "A": "≥ 80  — Ngày tốt. Cân bằng và năng suất cao.",
        "B": "≥ 65  — Ngày khá. Ổn định với vài điểm cần cải thiện.",
        "C": "≥ 50  — Trung bình. Một số trụ cột yếu rõ rệt.",
        "D": "≥ 35  — Dưới mức. Cần xem lại ưu tiên.",
        "F": "< 35  — Ngày khó khăn. Nghỉ ngơi và bắt đầu lại.",
    }
    for _, grade, colour in GRADE_THRESHOLDS:
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:6px;'>"
            f"<span style='font-family:Lora,serif; font-size:22px; font-weight:700;"
            f" color:{colour}; width:28px;'>{grade}</span>"
            f"<span style='font-size:13px; color:{THEME['text_muted']};'>{grade_descs[grade]}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # ── Mẹo nhập tài chính ──
    st.markdown(
        f"<h4 style='font-family:Lora,serif; color:{THEME['accent']};"
        f" margin:0 0 10px;'>💡 Mẹo nhập tài chính</h4>",
        unsafe_allow_html=True,
    )
    tips = [
        ("Phép tính trực tiếp", "Nhập `5000+3*1200` thay vì tính tay — app tự tính ra 8,600₩"),
        ("Đơn vị",              "Mặc định là ₩ (Won). Nếu dùng VNĐ, chỉ cần thêm một chữ số 0 vào FINANCE_REFERENCE trong config.py"),
        ("Income = 0",          "Những ngày không có thu nhập, cứ để 0 — không ảnh hưởng streak"),
    ]
    for title, tip in tips:
        st.markdown(
            f"<div style='background:{THEME['highlight']}; padding:8px 12px;"
            f" border-radius:8px; margin-bottom:6px; font-size:13px;'>"
            f"<strong>{title}:</strong>"
            f" <span style='color:{THEME['text_muted']};'>{tip}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


# =============================================================
# HÀM CHÍNH — GỌI TỪ life_tracker.py
# =============================================================

def render_dashboard(df: pd.DataFrame, summary: dict) -> None:
    """
    Vẽ toàn bộ dashboard 5 tab.

    Được gọi từ cuối life_tracker.py sau phần form nhập liệu.

    Tham số:
        df:      DataFrame toàn bộ dữ liệu (đã load và validated)
        summary: dict từ get_weekly_summary()
    """
    st.markdown("<hr style='margin:32px 0 20px;'>", unsafe_allow_html=True)
    st.markdown(
        f"<h3 style='font-family:Lora,serif; margin-bottom:18px;'>Dashboard</h3>",
        unsafe_allow_html=True,
    )

    # 5 tab — thêm GUIDE so với v0.5.x
    tab_score, tab_trends, tab_week, tab_db, tab_guide = st.tabs([
        "LIFE SCORE", "TRENDS", "THIS WEEK", "DATABASE", "HƯỚNG DẪN",
    ])

    with tab_score:
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        _tab_life_score(df)

    with tab_trends:
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        _tab_trends(df)

    with tab_week:
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        _tab_week(summary)

    with tab_db:
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        _tab_database(df)

    with tab_guide:
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        _tab_guide()
