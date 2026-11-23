from datetime import datetime, timedelta, timezone

from tests.conftest import auth_headers, make_user

R = "/api/v1/reservations"
RES = "/api/v1/resources"


def when(hours_from_now, length=2):
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    return start.isoformat(), (start + timedelta(hours=length)).isoformat()


def body(resource_id=24, length=2, **a):
    s, e = when(24, length)
    return {
        "resource_id": resource_id,
        "start_time": s,
        "end_time": e,
        "purpose": "Lab session",
        **a,
    }


def make_lab(client, staff_email="admin@x.com", code="LAB-1", **b):
    h = auth_headers(client, staff_email)
    return client.post(
        RES,
        json={"kind": "laboratory", "name": "Lab", "code": code, **b},
        headers=h,
    ).json()["id"]


def test_request_starts_pending_and_is_private(client, staff, db):
    lab = make_lab(client)
    stud = auth_headers(client, "stud@x.com")
    r = client.post(R, json=body(lab), headers=stud)

    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending"
    assert r.json()["user"]["email"] == "stud@x.com"
    rid = r.json()["id"]

    make_user(db, "other@x.com", "student")
    other = auth_headers(client, "other@x.com")

    assert client.get(R, headers=other).json() == []
    assert client.get(f"{R}/{rid}", headers=other).status_code == 403
    assert len(client.get(R, headers=stud).json()) == 1
    assert len(client.get(R, headers=auth_headers(client, "admin@x.com")).json()) == 1
    assert client.post(R, json=body(lab), status_code=401)
