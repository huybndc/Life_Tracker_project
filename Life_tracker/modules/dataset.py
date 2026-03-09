"""
=============================================================
File: dataset.py
Version: 0.6.0
Mục đích: Tầng Dữ Liệu — đọc/ghi/tính toán.

THAY ĐỔI TRONG v0.6.0:

1. FIX DRY VIOLATION:
   compute_life_score() và get_pillar_scores() trước đây
   viết lại cùng công thức 2 lần → nếu sửa 1 chỗ, dễ quên chỗ kia.
   Giờ cả 2 cùng gọi hàm nội bộ _compute_pillar_raw() dùng chung.

2. ATOMIC WRITE cho save_dataset():
   Ghi ra file .tmp trước → rename thành file chính.
   Nếu crash giữa chừng → file gốc vẫn còn nguyên.

3. Import GRADE_THRESHOLDS đưa lên đầu file (fix PEP 8).

4. Dùng hằng số từ config thay cho magic numbers.
=============================================================
"""

import csv
import os
import pandas as pd
from datetime import date, timedelta

# ─── FIX: tất cả import từ config ở ĐẦU FILE, không nằm trong hàm ───
from config import (
    DATA_PATH, COLUMNS, COLUMN_DEFAULTS,
    LEVEL_SCORES, EXERCISE_SCORES, LIFE_SCORE_WEIGHTS, GRADE_THRESHOLDS,
    SLEEP_OPTIMAL_HOURS, SLEEP_HOURS_NORMALIZER,
    SLEEP_HOURS_WEIGHT, SLEEP_QUALITY_WEIGHT,
    STUDY_MAX_HOURS, FINANCE_REFERENCE,
    SCORE_MESSAGES,
)


# =============================================================
# PHẦN 1: SCHEMA MIGRATION
# =============================================================

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Đảm bảo DataFrame có đầy đủ cột theo COLUMNS.

    - Nếu cột chưa có → tạo mới với giá trị mặc định
    - Nếu cột đã có nhưng có NaN → fill bằng giá trị mặc định

    Đây là schema migration tự động: người dùng không cần làm gì
    khi app được nâng cấp thêm cột mới.
    """
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = COLUMN_DEFAULTS.get(col, "")
        else:
            default = COLUMN_DEFAULTS.get(col, "")
            if default is not None:
                df[col] = df[col].fillna(default)
    return df[COLUMNS]


# =============================================================
# PHẦN 2: HÀM TÍNH ĐIỂM NỘI BỘ DÙNG CHUNG (FIX DRY)
# =============================================================

def _compute_pillar_raw(
    sleep_hours: float,
    sleep_quality: str,
    exercise: str,
    energy: str,
    study_hours: float,
    focus: str,
    spending: float,
    income: float,
) -> dict:
    """
    Hàm PRIVATE — tính điểm thô (0.0 → 1.0) cho từng trụ cột.

    TẠI SAO CẦN HÀM NÀY?
    Trước đây compute_life_score() và get_pillar_scores() viết
    cùng công thức 2 lần — vi phạm nguyên tắc DRY.
    Giờ cả 2 hàm đó đều GỌI hàm này → công thức chỉ tồn tại 1 nơi.

    Ví dụ nếu muốn đổi ngưỡng giờ ngủ lý tưởng từ 7.5 → 8.0:
    - Trước: phải sửa 2 chỗ trong 2 hàm khác nhau
    - Sau:   chỉ đổi SLEEP_OPTIMAL_HOURS trong config.py là xong

    Trả về:
        dict với các key = tên trụ cột, value = điểm thô [0.0, 1.0]
    """

    # ── SLEEP ──
    # Điểm giờ ngủ: tối đa khi đúng SLEEP_OPTIMAL_HOURS,
    # giảm tuyến tính khi xa ngưỡng đó (quá ít hoặc quá nhiều)
    sleep_h = max(0.0, min(1.0,
        1.0 - abs(sleep_hours - SLEEP_OPTIMAL_HOURS) / SLEEP_HOURS_NORMALIZER
    ))
    # Điểm chất lượng ngủ: chuyển chuỗi → [0.0, 1.0]
    # (score - 1) / 4 vì thang điểm 1-5, muốn ra 0-1
    sleep_q = (LEVEL_SCORES.get(sleep_quality, 3) - 1) / 4

    # ── ENERGY / FOCUS ── (cùng công thức, chỉ khác input)
    energy_raw = (LEVEL_SCORES.get(energy, 3) - 1) / 4
    focus_raw  = (LEVEL_SCORES.get(focus, 3) - 1) / 4

    # ── EXERCISE ──
    # EXERCISE_SCORES tối đa = 5 → chia 5 để chuẩn hoá
    exercise_raw = EXERCISE_SCORES.get(exercise, 0) / 5

    # ── STUDY ──
    # STUDY_MAX_HOURS = 10 → học 10h = điểm tối đa
    study_raw = min(study_hours / STUDY_MAX_HOURS, 1.0)

    # ── FINANCE ──
    # Trung tính tại net = 0 (điểm = 0.5)
    # FINANCE_REFERENCE = ngưỡng để đạt điểm tối đa / tối thiểu
    net = income - spending
    if net >= 0:
        finance_raw = min(0.5 + (net / FINANCE_REFERENCE) * 0.5, 1.0)
    else:
        finance_raw = max(0.5 + (net / FINANCE_REFERENCE) * 0.5, 0.0)

    return {
        "sleep":    sleep_h * SLEEP_HOURS_WEIGHT + sleep_q * SLEEP_QUALITY_WEIGHT,
        "sleep_h":  sleep_h,   # Lưu riêng để get_pillar_scores hiển thị đúng
        "sleep_q":  sleep_q,
        "energy":   energy_raw,
        "exercise": exercise_raw,
        "study":    study_raw,
        "focus":    focus_raw,
        "finance":  finance_raw,
    }


# =============================================================
# PHẦN 3: PUBLIC API — TÍNH ĐIỂM LIFE SCORE
# =============================================================

def compute_life_score(
    sleep_hours: float, sleep_quality: str,
    exercise: str, energy: str,
    study_hours: float, focus: str,
    spending: float, income: float,
) -> float:
    """
    Tính điểm Life Score tổng hợp (0 → 100).

    Gọi _compute_pillar_raw() để lấy điểm từng trụ cột,
    rồi nhân với trọng số tương ứng và cộng lại.

    Trả về: float, 1 chữ số thập phân, trong [0, 100]
    """
    raw = _compute_pillar_raw(
        sleep_hours, sleep_quality, exercise, energy,
        study_hours, focus, spending, income,
    )
    w = LIFE_SCORE_WEIGHTS

    total = (
        raw["sleep"]    * w["sleep"]    +
        raw["energy"]   * w["energy"]   +
        raw["exercise"] * w["exercise"] +
        raw["study"]    * w["study"]    +
        raw["focus"]    * w["focus"]    +
        raw["finance"]  * w["finance"]
    )
    return round(min(max(total * 100, 0), 100), 1)


def get_grade(score: float) -> tuple:
    """
    Chuyển điểm số → (chữ_xếp_hạng, màu_hex).

    Duyệt GRADE_THRESHOLDS từ cao xuống thấp,
    trả về ngưỡng đầu tiên mà score >= threshold.
    """
    for threshold, grade, colour in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade, colour
    return "F", "#9e9e9e"


def get_score_message(score: float) -> str:
    """
    Trả về thông điệp nhận xét tương ứng với điểm số.

    Trước đây hardcode trong life_tracker.py.
    Giờ đọc từ SCORE_MESSAGES trong config → dễ sửa nội dung.
    """
    for threshold, message in SCORE_MESSAGES:
        if score >= threshold:
            return message
    return SCORE_MESSAGES[-1][1]


def get_pillar_scores(
    sleep_hours: float, sleep_quality: str,
    exercise: str, energy: str,
    study_hours: float, focus: str,
    spending: float, income: float,
) -> dict:
    """
    Tính điểm 0-100 riêng lẻ cho từng trụ cột.
    Dùng để vẽ progress bars trong Life Score card.

    Gọi _compute_pillar_raw() dùng chung → không duplicate công thức.
    """
    raw = _compute_pillar_raw(
        sleep_hours, sleep_quality, exercise, energy,
        study_hours, focus, spending, income,
    )
    return {
        # Sleep kết hợp giờ và chất lượng theo tỷ lệ
        "Sleep":    round((raw["sleep_h"] * SLEEP_HOURS_WEIGHT
                          + raw["sleep_q"] * SLEEP_QUALITY_WEIGHT) * 100, 1),
        "Energy":   round(raw["energy"]   * 100, 1),
        "Exercise": round(raw["exercise"] * 100, 1),
        "Study":    round(raw["study"]    * 100, 1),
        "Focus":    round(raw["focus"]    * 100, 1),
        "Finance":  round(raw["finance"]  * 100, 1),
    }


# =============================================================
# PHẦN 4: ĐỌC / GHI DỮ LIỆU
# =============================================================

def load_dataset() -> pd.DataFrame:
    """
    Đọc CSV → DataFrame đã được validate và sắp xếp.

    Quy trình:
        1. Tạo file rỗng nếu chưa tồn tại
        2. Đọc CSV
        3. Migration schema (thêm cột thiếu, fill NaN)
        4. Parse cột date → datetime
        5. Sắp xếp theo ngày tăng dần
    """
    if not DATA_PATH.exists():
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(DATA_PATH, index=False)
        return df

    df = pd.read_csv(DATA_PATH)
    df = _ensure_columns(df)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

    return df


def save_dataset(df: pd.DataFrame) -> None:
    """
    Ghi DataFrame xuống CSV bằng kỹ thuật ATOMIC WRITE.

    VẤN ĐỀ CỦA CÁCH CŨ (ghi thẳng):
        df.to_csv(DATA_PATH)  ← nếu crash giữa chừng → file bị hỏng
        → Mất toàn bộ dữ liệu

    ATOMIC WRITE hoạt động như thế nào?
        1. Ghi ra file TẠM: life_log.csv.tmp
        2. Nếu ghi thành công → rename .tmp → .csv (thao tác nguyên tử)
        3. Nếu crash ở bước 1 → file .tmp bị hỏng, file .csv gốc vẫn nguyên
        4. os.replace(): rename an toàn, ghi đè file đích nếu đã tồn tại

    Kỹ thuật này giống cách Git và SQLite bảo vệ dữ liệu.

    Tham số bổ sung: quoting=csv.QUOTE_ALL
        Bọc tất cả giá trị trong dấu nháy kép.
        Lý do: cột "notes" có thể chứa dấu phẩy hoặc xuống dòng
        → nếu không quote, Excel hay pandas đọc lại sẽ bị vỡ cột.
    """
    # Đường dẫn file tạm — nằm cùng thư mục với file chính
    tmp_path = DATA_PATH.with_suffix(".csv.tmp")

    try:
        # Ghi ra file tạm với QUOTE_ALL để an toàn với dữ liệu text tự do
        df.to_csv(tmp_path, index=False, quoting=csv.QUOTE_ALL)

        # os.replace(): rename nguyên tử — thao tác này không thể bị ngắt
        # giữa chừng ở mức OS (trên hầu hết hệ điều hành)
        os.replace(tmp_path, DATA_PATH)

    except Exception as e:
        # Nếu có lỗi → xoá file tạm để không để lại rác
        if tmp_path.exists():
            tmp_path.unlink()
        # Re-raise lỗi để Streamlit hiển thị traceback
        raise e


# =============================================================
# PHẦN 5: ANALYTICS
# =============================================================

def get_streak(df: pd.DataFrame) -> int:
    """
    Đếm số ngày liên tiếp đã log (streak).

    Có grace period: nếu hôm nay chưa log nhưng hôm qua có,
    vẫn tính streak từ hôm qua → không mất streak buổi sáng.
    """
    if df.empty:
        return 0

    logged = set(df["date"].dt.date.unique())
    today  = date.today()
    streak, cursor = 0, today

    while cursor in logged:
        streak += 1
        cursor -= timedelta(days=1)

    if streak == 0:
        cursor = today - timedelta(days=1)
        while cursor in logged:
            streak += 1
            cursor -= timedelta(days=1)

    return streak


def get_weekly_summary(df: pd.DataFrame) -> dict:
    """
    Thống kê 7 ngày gần nhất.

    Lưu ý: dùng df.tail(7) theo số dòng, không phải 7 ngày lịch.
    Điều này đủ tốt cho use case hiện tại vì app enforce 1 dòng/ngày.
    """
    if df.empty:
        return {}

    week = df.tail(7).copy()
    week["energy_num"] = week["energy"].map(LEVEL_SCORES).fillna(3)

    return {
        "avg_sleep":     round(week["sleep_hours"].mean(), 1),
        "avg_study":     round(week["study_hours"].mean(), 1),
        "avg_energy":    round(week["energy_num"].mean(), 1),
        "total_spend":   week["spending"].sum(),
        "total_income":  week["income"].sum(),
        "net_balance":   week["income"].sum() - week["spending"].sum(),
        "exercise_days": int((week["exercise"] != "None").sum()),
        "avg_score":     round(week["life_score"].mean(), 1),
    }
