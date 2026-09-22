def test_login_with_valid_admin_credentials(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin1234"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["username"] == "admin"
    assert body["is_admin"] is True
    assert body["access_token"]


def test_login_with_valid_non_admin_credentials(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "user1", "password": "user1234"},
    )

    assert response.status_code == 200
    assert response.json()["is_admin"] is False


def test_login_with_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "user1", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_with_unknown_username(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "user1234"},
    )

    assert response.status_code == 401


def test_login_error_message_does_not_reveal_which_field_is_wrong(client):
    wrong_password = client.post(
        "/api/auth/login",
        json={"username": "user1", "password": "wrong-password"},
    )
    unknown_user = client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "user1234"},
    )

    assert wrong_password.json()["detail"] == unknown_user.json()["detail"]


def test_login_response_never_contains_password_hash(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "user1", "password": "user1234"},
    )

    assert "password_hash" not in response.text


def test_register_rejects_duplicate_username(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "user1", "password": "another1234"},
    )

    assert response.status_code == 409


def test_protected_endpoint_requires_a_token(client):
    assert client.get("/api/booking/").status_code == 401
    assert client.get("/api/booking/", headers={"Authorization": "Bearer broken"}).status_code == 401
