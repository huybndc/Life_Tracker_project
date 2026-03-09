"""
Version: 0.3.18
Module: config.py
Goal: Centralized Constant Management
"""

from pathlib import Path

# =========================================================
# FILE PATH CONFIGURATION
# =========================================================
DATA_FILE = "life_log.csv"
BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / DATA_FILE

# =========================================================
# DATASET SCHEMA (Updated v0.3.18)
# WHY: Adding 'spend_memo' and 'income_memo' to the schema 
#      ensures pandas knows what to expect during saving/loading.
# =========================================================
COLUMNS = [
    "date",
    "day_type",
    "sleep_hours",
    "sleep_quality",
    "exercise",
    "energy",
    "study_hours",
    "focus",
    "spending",
    "income",
    "spend_memo",  # ⭐ New in 0.3.17/18
    "income_memo", # ⭐ New in 0.3.17/18
    "notes"
]

# =========================================================
# DROPDOWN & SLIDER OPTIONS
# =========================================================

# WHAT: Qualitative metrics (Ordinal Data).
# WHY: We use 5 levels instead of 3 to provide better 
#      granularity for the Intelligence Dashboard charts.
LEVELS = ["Very Low", "Low", "Medium", "High", "Very High"]

EXERCISE_TYPES = ["None", "Walk", "Light", "Hard"]

DAY_TYPES = [
    "Study-heavy",
    "Work-heavy",
    "Mixed",
    "Rest/Holiday"
]