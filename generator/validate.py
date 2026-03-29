# generator/validate.py
from datetime import datetime


def _check_type(value, expected_type: str) -> bool:
    """Check if a value matches the expected type string."""
    if value is None:
        return True  # nulls are handled by dirty.py, not validation
    try:
        if expected_type == "int":
            int(value)
        elif expected_type == "float":
            float(value)
        elif expected_type == "bool":
            if str(value).lower() not in ("true", "false", "1", "0"):
                return False
        elif expected_type == "date":
            # Accept common date formats
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    datetime.strptime(str(value), fmt)
                    return True
                except ValueError:
                    continue
            return False
        # string always passes
        return True
    except (ValueError, TypeError):
        return False


def validate_rows(rows: list[dict], schema: dict) -> dict:
    """
    Validate generated rows against the schema.
    Returns a report dict with pass/fail counts and any issues found.
    """
    fields = {f["name"]: f["type"] for f in schema["fields"]}
    expected_fields = set(fields.keys())

    issues = []
    type_failures = 0
    missing_field_rows = 0
    extra_field_rows = 0

    for i, row in enumerate(rows):
        row_fields = set(row.keys())

        # Check for missing fields
        missing = expected_fields - row_fields
        if missing:
            missing_field_rows += 1
            issues.append(f"Row {i}: missing fields {missing}")

        # Check for extra fields
        extra = row_fields - expected_fields
        if extra:
            extra_field_rows += 1
            issues.append(f"Row {i}: unexpected fields {extra}")

        # Check types
        for field_name, expected_type in fields.items():
            if field_name in row:
                if not _check_type(row[field_name], expected_type):
                    type_failures += 1
                    issues.append(
                        f"Row {i}: field '{field_name}' expected {expected_type}, "
                        f"got '{row[field_name]}'"
                    )

    total_rows = len(rows)
    passed = total_rows - len(
        set(int(i.split(":")[0].replace("Row ", "")) for i in issues)
    ) if issues else total_rows

    report = {
        "total_rows":         total_rows,
        "passed_rows":        passed,
        "type_failures":      type_failures,
        "missing_field_rows": missing_field_rows,
        "extra_field_rows":   extra_field_rows,
        "issues":             issues[:10],  # cap at 10 to avoid noise
        "valid":              type_failures == 0 and missing_field_rows == 0
    }

    return report