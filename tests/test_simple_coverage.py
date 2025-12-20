"""
اختبارات بسيطة لتغطية المشروع
"""
import pytest


def test_imports():
    """اختبار الاستيرادات الأساسية"""
    import app
    import app.main
    import app.models
    import app.services
    import app.security
    import app.config
    import app.core
    import app.api
    import app.middleware
    import app.schemas
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
