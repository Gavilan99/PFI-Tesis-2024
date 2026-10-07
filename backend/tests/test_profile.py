"""GET and PATCH /api/users/me (RF07): the fields of UpdateProfileInput and no other."""

import pytest

from app.db.models import User
from tests.auth_helpers import USER_FIELDS, assert_error, registered


def test_get_me_returns_the_user_shape(api):
    user, headers = registered(api)
    response = api.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.get_json() == user
    assert set(response.get_json()) == USER_FIELDS


def test_patch_updates_every_editable_field(api, db_session):
    user, headers = registered(api)
    changes = {
        "displayName": "Nombre nuevo",
        "accountType": "salud",
        "ageRange": "25-34",
        "gender": "femenino",
        "country": "Argentina",
        "professionContext": "Psicóloga clínica",
    }

    response = api.patch("/api/users/me", headers=headers, json=changes)

    assert response.status_code == 200
    assert response.get_json() == {**user, **changes}
    assert api.get("/api/users/me", headers=headers).get_json() == {**user, **changes}
    row = db_session.get(User, user["id"])
    db_session.refresh(row)
    assert row.profession_context == "Psicóloga clínica"


def test_patch_only_touches_the_fields_sent(api):
    user, headers = registered(api)
    api.patch("/api/users/me", headers=headers, json={"country": "Uruguay", "gender": "otro"})

    response = api.patch("/api/users/me", headers=headers, json={"country": "Chile"})

    assert response.get_json() == {**user, "country": "Chile", "gender": "otro"}


def test_patch_with_null_or_empty_clears_an_optional_field(api):
    _, headers = registered(api)
    api.patch("/api/users/me", headers=headers, json={"country": "Uruguay", "accountType": "rrhh"})

    response = api.patch("/api/users/me", headers=headers, json={"country": "", "accountType": None})

    assert response.get_json()["country"] is None
    assert response.get_json()["accountType"] is None


def test_email_is_not_editable(api):
    user, headers = registered(api)
    response = api.patch("/api/users/me", headers=headers, json={"email": "otro@example.test"})
    assert_error(response, 400, "EMAIL_NOT_EDITABLE", "El email no se puede modificar.")
    assert api.get("/api/users/me", headers=headers).get_json()["email"] == user["email"]


@pytest.mark.parametrize(
    "body",
    [
        {"accountType": "admin"},
        {"accountType": "Salud"},
        {"id": "00000000-0000-0000-0000-000000000000"},
        {"isDeleted": True},
        {"cognitoSub": "x"},
        {"displayName": None},
        {"displayName": "   "},
        {"display_name": "snake_case is not the contract"},
        {"ageRange": "x" * 33},
    ],
    ids=["unknown-account-type", "account-type-case", "id", "is-deleted", "cognito-sub", "null-name",
         "blank-name", "snake-case-key", "too-long"],
)
def test_patch_rejects_anything_outside_update_profile_input(api, body):
    _, headers = registered(api)
    assert_error(api.patch("/api/users/me", headers=headers, json=body), 400, "VALIDATION_ERROR")


def test_patch_ignores_the_user_id_the_frontend_sends(api):
    alice, alice_headers = registered(api, username="Alice")
    bob, bob_headers = registered(api, username="Bob")

    response = api.patch(
        "/api/users/me", headers=alice_headers, json={"userId": bob["id"], "displayName": "Cambiado"}
    )

    assert response.status_code == 200
    assert response.get_json()["id"] == alice["id"]
    assert response.get_json()["displayName"] == "Cambiado"
    assert api.get("/api/users/me", headers=bob_headers).get_json()["displayName"] == "Bob"


def test_patch_with_an_empty_body_changes_nothing(api):
    user, headers = registered(api)
    response = api.patch("/api/users/me", headers=headers, json={})
    assert response.status_code == 200
    assert response.get_json() == user
