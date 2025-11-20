# tests/test_app.py


def test_app_fixture_loads_correctly(client):
    """
    Smoke test to ensure the app fixture loads correctly.
    """
    assert client.app is not None
    assert client.app.title == "CogniForge - Reality Kernel V3"
