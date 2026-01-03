# tests/test_app.py


def test_app_fixture_loads_correctly(client):
    """
    Smoke test to ensure the app fixture loads correctly.
    """
    # Get the app from the client
    import app.main
    test_app = app.main.app
    
    assert test_app is not None
    # The title comes from settings.PROJECT_NAME
    assert "CogniForge" in test_app.title
