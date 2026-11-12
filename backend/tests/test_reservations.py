from datetime import datetime, timedelta, timezone

from tests.conftest import auth_headers, make_user

R = "/api/v1/reservations"
RES = "/api/v1/resources"


def when(hours_from_now, length=2):
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    return start.isoformat(), (start + timedelta(hours=length)).isoformat()


def body(resource_id, h=24, length=2, **o):
    s, e = when(h, length)
    return {"resource_id": resource_id, "start_time": s, "end_time": e, "purpose": "Lab session", **o}


def make_lab(client, staff_email="admin@x.com", code="LAB-1", **o):
    h = auth_headers(client, staff_email)
    return client.post(RES, json={"kind": "laboratory", "name": "Lab", "code": code, **o}, headers=h).json()["id"]


def test_request_starts_pending_and_is_private(client, staff, db):
    lab = make_lab(client)
    stud = auth_headers(client, "stud@x.com")
    r = client.post(R, json=body(lab), headers=stud)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending" and r.json()["user"]["email"] == "stud@x.com"
    rid = r.json()["id"]

    make_user(db, "other@x.com", "student")
    other = auth_headers(client, "other@x.com")
    assert client.get(R, headers=other).json() == []            # others don't see it
    assert client.get(f"{R}/{rid}", headers=other).status_code == 404
    assert len(client.get(R, headers=stud).json()) == 1
    assert len(client.get(R, headers=auth_headers(client, "admin@x.com")).json()) == 1  # staff see all
    assert client.post(R, json=body(lab)).status_code == 401


def test_validation_rules(client, staff):
    lab = make_lab(client)
    stud = auth_headers(client, "stud@x.com")
    s, e = when(24)
    assert client.post(R, json={**body(lab), "start_time": e, "end_time": s}, headers=stud).status_code == 422
    assert client.post(R, json={**body(lab), "start_time": "2030-01-01T10:00:00"}, headers=stud).status_code == 422  # naive
    assert client.post(R, json=body(lab, h=-5), headers=stud).status_code == 400          # past
    assert client.post(R, json=body(lab, length=24 * 31), headers=stud).status_code == 400  # too long
    assert client.post(R, json=body(999), headers=stud).status_code == 404


def test_unavailable_resources_cannot_be_booked(client, staff):
    admin = auth_headers(client, "admin@x.com")
    lab = make_lab(client)
    stud = auth_headers(client, "stud@x.com")
    client.patch(f"{RES}/{lab}", json={"status": "maintenance"}, headers=admin)
    r = client.post(R, json=body(lab), headers=stud)
    assert r.status_code == 409 and "not available" in r.json()["detail"]


def test_approve_flow_and_overlap_protection(client, staff, db):
    lab = make_lab(client)
    admin = auth_headers(client, "admin@x.com")
    stud = auth_headers(client, "stud@x.com")
    fac = auth_headers(client, "fac@x.com")

    a = client.post(R, json=body(lab, h=24, length=3), headers=stud).json()["id"]
    b = client.post(R, json=body(lab, h=25, length=3), headers=fac).json()["id"]  # overlaps a
    assert client.post(f"{R}/{a}/approve", headers=stud).status_code == 403          # students can't approve
    ok = client.post(f"{R}/{a}/approve", json={"note": "ok"}, headers=admin)
    assert ok.status_code == 200 and ok.json()["status"] == "approved"
    assert ok.json()["reviewed_by"]["email"] == "admin@x.com"

    # b overlaps an approved booking -> cannot be approved; new overlapping requests refused
    assert client.post(f"{R}/{b}/approve", headers=admin).status_code == 409
    assert client.post(R, json=body(lab, h=26, length=1), headers=fac).status_code == 409
    # adjacent slot (starts exactly when a ends) is fine
    s, e = when(27, 2)
    assert client.post(R, json={**body(lab), "start_time": s, "end_time": e}, headers=fac).status_code == 201
    # double-approval blocked
    assert client.post(f"{R}/{a}/approve", headers=admin).status_code == 409

    assert client.post(f"{R}/{b}/reject", json={"note": "clash"}, headers=admin).json()["status"] == "rejected"
    assert client.post(f"{R}/{b}/cancel", headers=fac).status_code == 409           # already rejected

    # schedule shows busy slots (times only)
    sched = client.get(f"{R}/schedule/{lab}", headers=stud).json()
    assert len(sched) == 1 and set(sched[0]) == {"start_time", "end_time"}


def test_cancel_frees_the_slot(client, staff):
    lab = make_lab(client)
    admin = auth_headers(client, "admin@x.com")
    stud = auth_headers(client, "stud@x.com")
    fac = auth_headers(client, "fac@x.com")
    a = client.post(R, json=body(lab), headers=stud).json()["id"]
    client.post(f"{R}/{a}/approve", headers=admin)
    assert client.post(R, json=body(lab), headers=fac).status_code == 409
    assert client.post(f"{R}/{a}/cancel", headers=fac).status_code == 404            # not theirs
    assert client.post(f"{R}/{a}/cancel", headers=stud).json()["status"] == "cancelled"
    assert client.post(R, json=body(lab), headers=fac).status_code == 201


def test_staff_assign_directly(client, staff, db):
    lab = make_lab(client)
    fac_id = next(u["id"] for u in client.get("/api/v1/users", headers=auth_headers(client, "admin@x.com")).json()
                  if u["email"] == "fac@x.com")
    admin = auth_headers(client, "admin@x.com")
    r = client.post(f"{R}/assign", json={**body(lab), "user_id": fac_id}, headers=admin)
    assert r.status_code == 201 and r.json()["status"] == "approved" and r.json()["user"]["email"] == "fac@x.com"
    assert client.post(f"{R}/assign", json={**body(lab), "user_id": fac_id}, headers=admin).status_code == 409  # clash
    assert client.post(f"{R}/assign", json={**body(lab, h=60), "user_id": 999}, headers=admin).status_code == 400
    for email in ("stud@x.com", "fac@x.com", "lab@x.com"):
        assert client.post(f"{R}/assign", json={**body(lab, h=90), "user_id": fac_id},
                           headers=auth_headers(client, email)).status_code == 403
    # the assigned user sees it among their own
    assert len(client.get(R, headers=auth_headers(client, "fac@x.com")).json()) == 1


def test_lab_staff_review_equipment_only(client, staff):
    admin = auth_headers(client, "admin@x.com")
    lab = make_lab(client)
    eq = client.post(RES, json={"kind": "equipment", "name": "Scope", "code": "EQ-1"}, headers=admin).json()["id"]
    stud = auth_headers(client, "stud@x.com")
    labs = auth_headers(client, "lab@x.com")
    r_lab = client.post(R, json=body(lab), headers=stud).json()["id"]
    r_eq = client.post(R, json=body(eq), headers=stud).json()["id"]
    assert client.post(f"{R}/{r_lab}/approve", headers=labs).status_code == 403
    assert client.post(f"{R}/{r_eq}/approve", headers=labs).status_code == 200


def test_monitor_overview(client, staff):
    admin = auth_headers(client, "admin@x.com")
    lab = make_lab(client)
    bad = make_lab(client, code="LAB-2")
    client.patch(f"{RES}/{bad}", json={"status": "damaged"}, headers=admin)
    stud = auth_headers(client, "stud@x.com")
    now_id = client.post(f"{R}/assign", json={**body(lab, h=0, length=2), "user_id": 5}, headers=admin)
    soon = client.post(R, json=body(lab, h=5, length=1), headers=stud).json()["id"]
    client.post(f"{R}/{soon}/approve", headers=admin)
    client.post(R, json=body(lab, h=48, length=1), headers=stud)  # stays pending

    m = client.get("/api/v1/monitor", headers=admin).json()
    s = m["summary"]
    assert now_id.status_code == 201, now_id.text
    assert s["total_resources"] == 2 and s["damaged"] == 1
    assert s["in_use_now"] == 1 and s["starting_next_24h"] == 1 and s["pending_requests"] == 1
    assert m["in_use_now"][0]["resource"]["code"] == "LAB-1"
    assert m["needs_attention"][0]["code"] == "LAB-2"
    assert client.get("/api/v1/monitor", headers=stud).status_code == 403
    assert client.get("/api/v1/monitor", headers=auth_headers(client, "lab@x.com")).status_code == 200
