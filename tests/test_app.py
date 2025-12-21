# tests/test_app.py


def test_app_fixture_loads_correctly(client, test_app):
    """
    Smoke test to ensure the app fixture loads correctly.
    """
    assert test_app is not None
    # The title comes from settings.PROJECT_NAME
    assert "CogniForge" in test_app.title
