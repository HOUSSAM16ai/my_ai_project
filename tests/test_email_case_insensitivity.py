import pytest


@pytest.mark.asyncio
async def test_email_case_insensitivity(client):
    # 1. Register with mixed case email
    email = "MixedCase@Example.com"
    lowercase_email = email.lower()
    password = "password123"
    payload = {"full_name": "Test User", "email": email, "password": password}

    response = client.post("/api/security/register", json=payload)
    assert response.status_code == 200, f"Registration failed: {response.text}"

    # 2. Try to register with lowercase email (should fail as duplicate)
    payload_lower = {"full_name": "Test User 2", "email": lowercase_email, "password": password}
    response = client.post("/api/security/register", json=payload_lower)
    # The bug is that it currently SUCCEEDS (200) because they are treated as different users
    # We expect 400 after the fix.
    # For verification of the BUG, we assert that it FAILS to detect duplicate (i.e. returns 200).
    # Wait, if I want to "prove the bug is resolved", I should write the test expecting the CORRECT behavior,
    # and it should FAIL now.

    # So I expect 400. It will fail now (return 200).
    assert response.status_code == 400, "Should detect duplicate email regardless of case"

    # 3. Login with lowercase email
    login_payload = {"email": lowercase_email, "password": password}
    response = client.post("/api/security/login", json=login_payload)
    # This currently fails (401) because of case sensitivity mismatch
    assert response.status_code == 200, "Should allow login with lowercase email"
