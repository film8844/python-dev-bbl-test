def book(client, headers, slot, note=None):
    return client.post("/api/booking/", json={"slot": slot, "note": note}, headers=headers)


def test_non_admin_can_create_a_booking(client, user1):
    response = book(client, user1, "10am-11am", "morning check-up")
    body = response.json()

    assert response.status_code == 201
    assert body["slot"] == "10am-11am"
    assert body["username"] == "user1"


def test_booking_owner_comes_from_the_token_not_the_request(client, user1):
    response = client.post(
        "/api/booking/",
        json={"slot": "10am-11am", "user_id": 999},
        headers=user1,
    )

    assert response.status_code == 201
    assert response.json()["username"] == "user1"


def test_slot_must_be_one_of_the_available_slots(client, user1):
    assert book(client, user1, "any time please").status_code == 400


def test_a_slot_cannot_be_booked_twice(client, user1, user2):
    assert book(client, user1, "10am-11am").status_code == 201
    assert book(client, user2, "10am-11am").status_code == 409


def test_cancelling_a_booking_frees_the_slot(client, user1, user2):
    booking_id = book(client, user1, "10am-11am").json()["id"]

    assert client.delete(f"/api/booking/{booking_id}", headers=user1).status_code == 200
    assert book(client, user2, "10am-11am").status_code == 201


def test_non_admin_only_sees_their_own_bookings(client, user1, user2):
    book(client, user1, "10am-11am")
    book(client, user2, "01pm-02pm")

    bookings = client.get("/api/booking/", headers=user1).json()

    assert len(bookings) == 1
    assert bookings[0]["username"] == "user1"


def test_admin_sees_every_booking(client, admin, user1, user2):
    book(client, user1, "10am-11am")
    book(client, user2, "01pm-02pm")

    bookings = client.get("/api/booking/", headers=admin).json()

    assert len(bookings) == 2
    assert {item["username"] for item in bookings} == {"user1", "user2"}


def test_only_admin_can_use_the_all_bookings_endpoint(client, admin, user1):
    book(client, user1, "10am-11am")

    assert client.get("/api/booking/all", headers=admin).status_code == 200
    assert client.get("/api/booking/all", headers=user1).status_code == 403


def test_non_admin_cannot_read_another_users_booking(client, user1, user2):
    booking_id = book(client, user1, "10am-11am").json()["id"]

    assert client.get(f"/api/booking/{booking_id}", headers=user2).status_code == 403


def test_non_admin_cannot_change_another_users_booking(client, user1, user2):
    booking_id = book(client, user1, "10am-11am", "mine").json()["id"]

    response = client.patch(
        f"/api/booking/{booking_id}",
        json={"note": "hacked"},
        headers=user2,
    )

    assert response.status_code == 403
    assert client.get(f"/api/booking/{booking_id}", headers=user1).json()["note"] == "mine"


def test_non_admin_cannot_cancel_another_users_booking(client, user1, user2):
    booking_id = book(client, user1, "10am-11am").json()["id"]

    assert client.delete(f"/api/booking/{booking_id}", headers=user2).status_code == 403
    assert client.get(f"/api/booking/{booking_id}", headers=user1).json()["status"] == "booked"


def test_non_admin_can_manage_their_own_booking(client, user1):
    booking_id = book(client, user1, "10am-11am").json()["id"]

    updated = client.patch(
        f"/api/booking/{booking_id}",
        json={"note": "updated"},
        headers=user1,
    )
    cancelled = client.delete(f"/api/booking/{booking_id}", headers=user1)

    assert updated.status_code == 200
    assert updated.json()["note"] == "updated"
    assert cancelled.json()["status"] == "cancelled"


def test_admin_can_manage_a_booking_owned_by_someone_else(client, admin, user1):
    booking_id = book(client, user1, "10am-11am").json()["id"]

    response = client.patch(
        f"/api/booking/{booking_id}",
        json={"note": "moved by admin"},
        headers=admin,
    )

    assert response.status_code == 200
    assert response.json()["username"] == "user1"


def test_booking_responses_never_contain_password_hash(client, admin, user1):
    book(client, user1, "10am-11am")

    assert "password_hash" not in client.get("/api/booking/", headers=user1).text
    assert "password_hash" not in client.get("/api/booking/all", headers=admin).text
