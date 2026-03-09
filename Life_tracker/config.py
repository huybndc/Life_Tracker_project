"""
=============================================================
File: config.py
Version: 0.6.0
Mục đích: Single Source of Truth — toàn bộ hằng số của app.

THAY ĐỔI TRONG v0.6.0:
- Thêm các magic number thành hằng số có tên rõ ràng:
    SLEEP_OPTIMAL_HOURS, SLEEP_HOURS_NORMALIZER
    FINANCE_REFERENCE, SLEEP_HOURS_WEIGHT, SLEEP_QUALITY_WEIGHT
    STUDY_MAX_HOURS
- Thêm SCORE_MESSAGES cho thông điệp Life Score
- Thêm PILLAR_COLORS tập trung (tránh hardcode màu rải rác)

NGUYÊN TẮC THIẾT KẾ:
    Nếu cùng một giá trị xuất hiện ở 2 chỗ trở lên → đưa vào đây.
    "Single Source of Truth" nghĩa là chỉ có 1 nơi quyết định.
=============================================================
"""

from pathlib import Path


# =============================================================
# PHẦN 1: ĐƯỜNG DẪN FILE
# =============================================================

DATA_FILE = "life_log.csv"
BASE_DIR  = Path(__file__).parent
DATA_PATH = BASE_DIR / DATA_FILE


# =============================================================
# PHẦN 2: SCHEMA DỮ LIỆU
# =============================================================

COLUMNS = [
    "date", "day_type",
    "sleep_hours", "sleep_quality",
    "exercise", "energy",
    "study_hours", "focus",
    "spending", "income", "spend_memo", "income_memo",
    "notes", "life_score",
]

COLUMN_DEFAULTS = {
    "date":          None,
    "day_type":      "Mixed",
    "sleep_hours":   7,
    "sleep_quality": "Medium",
    "exercise":      "None",
    "energy":        "Medium",
    "study_hours":   0,
    "focus":         "Medium",
    "spending":      0.0,
    "income":        0.0,
    "spend_memo":    "",
    "income_memo":   "",
    "notes":         "",
    "life_score":    0.0,
}


# =============================================================
# PHẦN 3: TUỲ CHỌN DROPDOWN / SLIDER
# =============================================================

LEVELS         = ["Very Low", "Low", "Medium", "High", "Very High"]
EXERCISE_TYPES = ["None", "Walk", "Light", "Hard"]
DAY_TYPES      = ["Study-heavy", "Work-heavy", "Mixed", "Rest/Holiday"]

LEVEL_SCORES = {
    "Very Low": 1, "Low": 2, "Medium": 3, "High": 4, "Very High": 5,
}
EXERCISE_SCORES = {
    "None": 0, "Walk": 2, "Light": 3, "Hard": 5,
}


# =============================================================
# PHẦN 4: HẰNG SỐ CÔNG THỨC LIFE SCORE
# =============================================================
# --- v0.6.0: Tất cả "magic number" trước đây đều được đặt tên ---

# Giờ ngủ lý tưởng (điểm tối đa khi ngủ đúng số giờ này)
SLEEP_OPTIMAL_HOURS = 7.5

# Hệ số chuẩn hoá giờ ngủ:
# công thức: 1 - abs(hours - OPTIMAL) / NORMALIZER
# khi hours = 0  → score = 1 - 7.5/7.5 = 0.0 (tệ nhất)
# khi hours = 7.5 → score = 1 - 0/7.5  = 1.0 (tốt nhất)
SLEEP_HOURS_NORMALIZER = 7.5

# Tỷ lệ kết hợp 2 thành phần của Sleep
SLEEP_HOURS_WEIGHT   = 0.6   # Giờ ngủ đóng góp 60% điểm Sleep
SLEEP_QUALITY_WEIGHT = 0.4   # Chất lượng ngủ đóng góp 40% điểm Sleep

# Điểm tối đa khi học đủ số giờ này trở lên
STUDY_MAX_HOURS = 10

# Ngưỡng tài chính tham chiếu (đơn vị ₩)
# net = +200_000₩ → điểm tài chính = 1.0 (tối đa)
# net = -200_000₩ → điểm tài chính = 0.0 (tối thiểu)
# Điều chỉnh con số này nếu mức thu chi hàng ngày của bạn khác
FINANCE_REFERENCE = 200_000

# Trọng số các trụ cột (phải cộng lại = 1.0)
LIFE_SCORE_WEIGHTS = {
    "sleep":    0.25,
    "energy":   0.20,
    "exercise": 0.15,
    "study":    0.20,
    "focus":    0.10,
    "finance":  0.10,
}


# =============================================================
# PHẦN 5: XẾP HẠNG
# =============================================================

GRADE_THRESHOLDS = [
    (90, "S", "#7c9e87"),
    (80, "A", "#7b9ebd"),
    (65, "B", "#9b8ec4"),
    (50, "C", "#c4a86e"),
    (35, "D", "#c47e7e"),
    (0,  "F", "#9e9e9e"),
]

# Thông điệp tương ứng với từng mức điểm
# Trước đây hardcode trong life_tracker.py — giờ tập trung ở đây
# Mỗi tuple: (ngưỡng điểm tối thiểu, thông điệp)
SCORE_MESSAGES = [
    (90, "Ngày xuất sắc. Bạn đang ở đỉnh phong độ."),
    (80, "Cân bằng tốt trên tất cả các trụ cột."),
    (65, "Ngày ổn định — vẫn còn dư địa để phát triển."),
    (50, "Trung bình — một vài trụ cột cần chú ý hơn."),
    (35, "Dưới mức trung bình. Nghỉ ngơi và suy ngẫm."),
    (0,  "Ngày khó khăn. Ngày mai là khởi đầu mới."),
]

# Gợi ý cải thiện khi điểm trụ cột thấp (< 40 điểm)
# Hiển thị trong Life Score card để người dùng biết cần làm gì
PILLAR_TIPS = {
    "Sleep":    "Thử đi ngủ trước 23h và tắt màn hình 30 phút trước khi ngủ.",
    "Energy":   "Uống đủ nước, ăn đủ bữa, và ra ngoài hít thở không khí.",
    "Exercise": "Chỉ cần 15 phút đi bộ cũng đã tính là vận động.",
    "Study":    "Thử kỹ thuật Pomodoro: 25 phút học, 5 phút nghỉ.",
    "Focus":    "Tắt thông báo điện thoại khi học và dọn dẹp bàn làm việc.",
    "Finance":  "Ghi lại mọi khoản chi — nhận thức là bước đầu tiên.",
}


# =============================================================
# PHẦN 6: MÀU SẮC TỪNG TRỤ CỘT
# =============================================================
# Trước đây hardcode rải rác trong life_tracker.py
# Giờ tập trung ở đây → đổi màu 1 chỗ, tự động cập nhật khắp nơi

PILLAR_COLORS = {
    "Sleep":    "#5c7a6b",   # Xanh sage
    "Energy":   "#7a9e8e",   # Xanh sage nhạt
    "Exercise": "#c07860",   # Cam đất
    "Study":    "#7a6aaa",   # Tím lavender
    "Focus":    "#b08888",   # Hồng đất
    "Finance":  "#5a7a5a",   # Xanh rừng
}


# =============================================================
# PHẦN 7: BẢNG MÀU GIAO DIỆN
# =============================================================

THEME = {
    "bg":         "#f5f2ee",
    "surface":    "#eee8df",
    "surface2":   "#e5ddd0",
    "border":     "#c9bfb0",
    "accent":     "#5c7a6b",
    "accent2":    "#7a9e8e",
    "accent3":    "#a07850",
    "text":       "#3a3028",
    "text_muted": "#7a6e62",
    "success":    "#5a7a5a",
    "warning":    "#c07860",
    "danger":     "#b06060",
    "purple":     "#7a6aaa",
    "highlight":  "#e8e2d8",
}
