"""
اختبارات حالة النواة (Kernel State).

تهدف هذه الاختبارات إلى ضمان تطبيق حالة التطبيق
على كائن FastAPI بطريقة صريحة ومتسقة.
"""

from fastapi import FastAPI

from app.core.kernel_state import apply_app_state, build_app_state


class TestKernelState:
    """اختبارات تطبيق حالة النواة."""

    def test_apply_app_state_sets_expected_attributes(self) -> None:
        """يتحقق من أن حالة التطبيق تُطبّق على كائن FastAPI بالكامل."""
        app = FastAPI()
        state = build_app_state()

        apply_app_state(app, state)

        for key, value in state.as_mapping().items():
            assert getattr(app.state, key) is value
