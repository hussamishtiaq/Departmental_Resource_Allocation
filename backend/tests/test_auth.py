from app.core.security import create_access_token
from tests.conftest import PASSWORD, auth_headers, make_user

API = "/api/v1"


def register(client, **over):
    body = {"full_name": "Ali Khan", "email": "ali@x.com", "password": PASSWORD}
    body.update(over)
    return client.post(f"{API}/auth/register", json=body)


def test_register_creates_student_only(client):
    r = register(client, role="hod")  # extra field must be ignored
    assert r.status_code == 201
    assert r.json()["role"]["name"] == "student"
    assert "hashed_password" not in r.json()


def test_register_works_on_fresh_database_without_roles(client, db):
    from app.models import Role
    db.query(Role).delete()
    db.commit()
    assert register(client).status_code == 201


def test_register_duplicate_email_case_insensitive(client):
    assert register(client).status_code == 201
    assert register(client, email="ALI@x.com").status_code == 409


def test_register_weak_password(client):
    assert register(client, password="short1").status_code == 422
    assert register(client, password="onlyletters").status_code == 422


def test_login_me_flow_and_permissions(client, staff):
    me = client.get(f"{API}/auth/me", headers=auth_headers(client, "stud@x.com")).json()
    assert me["permissions"] == ["reservations:create", "resources:read"]
    assert me["assignable_roles"] == []
    hod = client.get(f"{API}/auth/me", headers=auth_headers(client, "hod@x.com")).json()
    assert "department:manage" in hod["permissions"]
    assert set(hod["assignable_roles"]) == {"hod", "department_admin", "lab_staff", "faculty", "student"}


def test_login_failures(client, db):
    register(client)
    bad = client.post(f"{API}/auth/login", data={"username": "ali@x.com", "password": "nope12345"})
    unknown = client.post(f"{API}/auth/login", data={"username": "no@x.com", "password": PASSWORD})
    assert bad.status_code == unknown.status_code == 401
    make_user(db, "off@x.com", active=False)
    off = client.post(f"{API}/auth/login", data={"username": "off@x.com", "password": PASSWORD})
    assert off.status_code == 403


def test_protected_routes_reject_missing_or_bad_token(client):
    assert client.get(f"{API}/auth/me").status_code == 401
    assert client.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    expired = {"Authorization": f"Bearer {create_access_token(1, expires_minutes=-1)}"}
    assert client.get(f"{API}/auth/me", headers=expired).status_code == 401


def test_deactivated_user_token_stops_working(client, db):
    u = make_user(db, "t@x.com")
    h = auth_headers(client, "t@x.com")
    u.is_active = False
    db.commit()
    assert client.get(f"{API}/auth/me", headers=h).status_code == 401


def _id(client, h, email):
    return next(u["id"] for u in client.get(f"{API}/users", headers=h).json() if u["email"] == email)


def test_users_endpoints_need_permission(client, staff):
    for email in ("lab@x.com", "fac@x.com", "stud@x.com"):
        assert client.get(f"{API}/users", headers=auth_headers(client, email)).status_code == 403
    assert len(client.get(f"{API}/users", headers=auth_headers(client, "admin@x.com")).json()) == 5


def test_role_hierarchy_rules(client, staff):
    hod = auth_headers(client, "hod@x.com")
    admin = auth_headers(client, "admin@x.com")
    stud, lab, fac, hod_id = (_id(client, hod, e) for e in
                              ("stud@x.com", "lab@x.com", "fac@x.com", "hod@x.com"))
    patch = lambda h, uid, **b: client.patch(f"{API}/users/{uid}", json=b, headers=h)

    # admin may promote a student up to lab_staff (below admin) ...
    assert patch(admin, stud, role="lab_staff").json()["role"]["name"] == "lab_staff"
    # ... but not to its own level or above
    assert patch(admin, stud, role="department_admin").status_code == 403
    assert patch(admin, stud, role="hod").status_code == 403
    # ... and cannot touch users at/above its level
    assert patch(admin, hod_id, role="student").status_code == 403
    assert patch(admin, hod_id, is_active=False).status_code == 403
    # lab staff and below can't manage at all
    assert patch(auth_headers(client, "lab@x.com"), fac, role="student").status_code == 403
    # HOD can appoint an administrator and unknown roles are rejected
    assert patch(hod, fac, role="department_admin").status_code == 200
    assert patch(hod, fac, role="bogus").status_code == 400
    assert patch(hod, lab, is_active=False).json()["is_active"] is False
    assert client.post(f"{API}/auth/login", data={"username": "lab@x.com", "password": PASSWORD}).status_code == 403


def test_cannot_change_own_account(client, staff):
    hod = auth_headers(client, "hod@x.com")
    me = _id(client, hod, "hod@x.com")
    assert client.patch(f"{API}/users/{me}", json={"role": "student"}, headers=hod).status_code == 400
    assert client.patch(f"{API}/users/{me}", json={"is_active": False}, headers=hod).status_code == 400
