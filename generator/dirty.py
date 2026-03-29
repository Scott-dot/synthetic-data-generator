# generator/dirty.py
import random
import copy
from config import DIRTY_CONFIG


def _is_numeric(value) -> bool:
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def _inject_outlier(value, multiplier_range: tuple = (5, 15)):
    """Multiply a numeric value by a random factor to create an outlier."""
    if _is_numeric(value):
        multiplier = random.uniform(*multiplier_range)
        try:
            if isinstance(value, int):
                return int(float(value) * multiplier)
            return round(float(value) * multiplier, 2)
        except (ValueError, TypeError):
            return value
    return value


def inject_dirty_data(rows: list[dict], config: dict = None) -> tuple[list[dict], dict]:
    """
    Post-generation pass that injects configurable noise into rows.

    Dirty types:
    - Outliers: numeric values multiplied by 5-15x
    - Nulls: fields set to None
    - Duplicates: rows duplicated and appended

    Returns modified rows and a report of what was injected.
    """
    if config is None:
        config = DIRTY_CONFIG

    if not config.get("enabled", False):
        return rows, {"dirty_data_enabled": False}

    rows = copy.deepcopy(rows)
    total = len(rows)

    outlier_count = 0
    null_count = 0
    duplicate_count = 0

    # Inject outliers
    outlier_n = max(1, int(total * config.get("outlier_rate", 0.02)))
    outlier_indices = random.sample(range(total), min(outlier_n, total))

    for i in outlier_indices:
        row = rows[i]
        # Pick a random numeric field in this row
        numeric_fields = [k for k, v in row.items() if _is_numeric(v)]
        if numeric_fields:
            field = random.choice(numeric_fields)
            original = rows[i][field]
            rows[i][field] = _inject_outlier(original)
            outlier_count += 1

    # Inject nulls
    null_n = max(1, int(total * config.get("null_rate", 0.01)))
    null_indices = random.sample(range(total), min(null_n, total))

    for i in null_indices:
        row = rows[i]
        field = random.choice(list(row.keys()))
        rows[i][field] = None
        null_count += 1

    # Inject duplicates
    dup_n = max(1, int(total * config.get("duplicate_rate", 0.01)))
    dup_indices = random.sample(range(total), min(dup_n, total))

    duplicates = [copy.deepcopy(rows[i]) for i in dup_indices]
    rows.extend(duplicates)
    duplicate_count = len(duplicates)

    report = {
        "dirty_data_enabled": True,
        "outliers_injected":  outlier_count,
        "nulls_injected":     null_count,
        "duplicates_injected": duplicate_count,
        "final_row_count":    len(rows)
    }

    return rows, report