import warnings

import pytest
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import configure_mappers

from app.models import Mission


def test_circular_dependency_drop():
    """
    Verifies that tables can be sorted for dropping without circular dependency warnings.
    """
    configure_mappers()
    metadata = Mission.metadata

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always", SAWarning)  # Cause all warnings to always be triggered.
        # Accessing sorted_tables triggers the topological sort which emits the warning if cycles exist
        _ = metadata.sorted_tables

        # Check if we caught the specific circular dependency warning
        cycle_warnings = [
            w
            for w in record
            if issubclass(w.category, SAWarning)
            and ("unresolvable cycles" in str(w.message) or "Can't sort tables" in str(w.message))
        ]

        if cycle_warnings:
            pytest.fail(f"Circular dependency detected: {cycle_warnings[0].message}")
