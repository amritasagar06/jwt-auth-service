def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "testuser@example.com", "username": "testuser", "password": "Password123"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@example.com"

def test_login_user(client):
    # Register first
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "username": "loginuser", "password": "Password123"}
    )
    # Now try to login
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "Password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()