"""
Version: 0.3

# =========================================================
# ⭐ STRUCTURE IMPROVEMENT (0.3.5 REVIEW)
# =========================================================
# This module handles all dataset operations.
#
# WHY THIS FILE EXISTS:
# Instead of mixing data logic with UI logic,
# we isolate dataset handling here.
#
# This follows a common architecture pattern:
#
# UI Layer → Logic Layer → Data Layer
#
# In our case:
#
# main.py → ui_sections → dataset module → CSV file
"""

# =========================================================
# IMPORTS
# =========================================================

import pandas as pd

from config import DATA_PATH, COLUMNS


# =========================================================
# DATASET FUNCTIONS
# =========================================================

def load_dataset():
    """
    WHAT:
    Load dataset từ file CSV.

    WHY:
    Nếu file chưa tồn tại (lần đầu chạy app),
    ta tạo dataset rỗng với schema chuẩn.

    STEP BY STEP LOGIC:

    1️⃣ Check if CSV exists
    2️⃣ If not → create empty dataset
    3️⃣ Load CSV
    4️⃣ Convert date column
    5️⃣ Sort dataset
    """

    # =========================================================
    # ⭐ STRUCTURE IMPROVEMENT
    # =========================================================
    # Using pathlib instead of os.path
    # DATA_PATH is a Path object
    # =========================================================

    if not DATA_PATH.exists():

        # Tạo dataframe rỗng với đúng columns
        df = pd.DataFrame(columns=COLUMNS)

        # Lưu xuống CSV
        df.to_csv(DATA_PATH, index=False)

    # Load dataset
    df = pd.read_csv(DATA_PATH)

    # -------------------------------------------------
    # Convert date column
    # -------------------------------------------------

    # ⚠ BUG FIX (from previous version)
    #
    # Without converting to datetime,
    # sorting dates may behave incorrectly.
    #
    # Example of wrong order:
    # 2024-10-1
    # 2024-2-5
    #
    # Datetime ensures proper chronological sorting.

    if len(df) > 0:

        df["date"] = pd.to_datetime(df["date"])

        # Sort theo date để dashboard luôn đúng
        df = df.sort_values("date")

    return df



def save_dataset(df):
    """
    Lưu dataset xuống CSV.

    TIP:
    index=False để tránh pandas tạo thêm
    cột index thừa trong file CSV.
    """

    df.to_csv(DATA_PATH, index=False)