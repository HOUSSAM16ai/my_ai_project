# Solution for FlexibleEnum Case Sensitivity (CogniForge)

## Overview

This solution resolves the `LookupError: 'USER' is not among the defined enum values` issue encountered when migrating to FastAPI/SQLModel with Supabase PostgreSQL.

The core issue was that Supabase/PostgreSQL stores Enum values in UPPERCASE (e.g., `USER`) by default or due to legacy data, while the Python Enum definitions are in lowercase (e.g., `user`). Standard SQLAlchemy Enum types perform strict validation upon retrieval, causing a crash when casing mismatches occur.

## The Solution

We implemented a robust dual-layer solution:

### 1. `CaseInsensitiveEnum` (Python Layer)
A base Enum class that implements `_missing_` to handle case-insensitive lookups during instantiation.

```python
class CaseInsensitiveEnum(str, enum.Enum):
    @classmethod
    def _missing_(cls, value):
        # Tries uppercase lookup, then value matching
        ...
```

### 2. `FlexibleEnum` (SQLAlchemy Layer)
A `TypeDecorator` that wraps the SQLAlchemy `Text` type (for storage) but uses the `CaseInsensitiveEnum` logic for retrieval. This bypasses SQLAlchemy's strict Enum validation while preserving the ability to map database values back to Python Enum objects correctly.

```python
class FlexibleEnum(TypeDecorator):
    impl = Text
    ...
    def process_result_value(self, value, dialect):
        return self._enum_type(value)  # Triggers _missing_
```

## Applied Changes

1.  **`app/models.py`**:
    *   Added `FlexibleEnum` class definition.
    *   Applied `FlexibleEnum(EnumType)` to all Enum fields in `AdminMessage`, `Mission`, `Task`, `MissionPlan`, and `MissionEvent`.
    *   Verified `CaseInsensitiveEnum` implementation.

2.  **`tests/unit/test_enum_case_sensitivity.py`**:
    *   Created a comprehensive test suite covering:
        *   Enum lookup logic (Lower, Upper, Mixed case).
        *   Database integration (SQLite Async).
        *   **Simulation of Supabase Behavior**: Explicitly inserting `USER` (uppercase) via raw SQL and verifying correct retrieval via ORM.

3.  **`scripts/heal_db_enum_case.py`**:
    *   Created an async maintenance script to scan the database for uppercase Enum values and convert them to lowercase.
    *   Supports `--dry-run` (default) and `--fix` modes.

## Verification

Run the verification tests:
```bash
python -m pytest tests/unit/test_enum_case_sensitivity.py
```

Run the repair script (Dry Run):
```bash
python scripts/heal_db_enum_case.py --dry-run
```
