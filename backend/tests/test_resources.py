from tests.conftest import auth_headers

API = "/api/v1/resources"


def lab(**o):
    return {"kind": "laboratory", "name": "Computer Lab", "code": "lab-1", "capacity": 30, **o}


def equip(**o):
    return {"kind": "equipment", "name": "Projector", "code": "eq-1", "serial_number": "S1", **o}


def test_create_read_and_code_normalised(client, staff):
    admin = auth_headers(client, "admin@x.com")
    r = client.post(API, json=lab(), headers=admin)
    assert r.status_code == 201, r.text
    assert r.json()["code"] == "LAB-1" and r.json()["status"] == "available"
    stud = auth_headers(client, "stud@x.com")
    assert client.get(f"{API}/{r.json()['id']}", headers=stud).json()["name"] == "Computer Lab"
    assert client.get(f"{API}/999", headers=stud).status_code == 404


def test_authorization(client, staff):
    assert client.post(API, json=lab()).status_code == 401
    for email in ("fac@x.com", "stud@x.com"):
        assert client.post(API, json=lab(), headers=auth_headers(client, email)).status_code == 403
    labs = auth_headers(client, "lab@x.com")
    # lab staff: equipment yes, rooms/labs no
    assert client.post(API, json=lab(), headers=labs).status_code == 403
    assert client.post(API, json=equip(), headers=labs).status_code == 201


def test_lab_staff_cannot_edit_or_delete_rooms(client, staff):
    admin = auth_headers(client, "admin@x.com")
    labs = auth_headers(client, "lab@x.com")
    rid = client.post(API, json=lab(), headers=admin).json()["id"]
    assert client.patch(f"{API}/{rid}", json={"name": "x"}, headers=labs).status_code == 403
    assert client.delete(f"{API}/{rid}", headers=labs).status_code == 403


def test_hierarchy_rules(client, staff):
    admin = auth_headers(client, "admin@x.com")
    room = client.post(API, json=lab(), headers=admin).json()
    eq = client.post(API, json=equip(parent_id=room["id"]), headers=admin)
    assert eq.status_code == 201 and eq.json()["parent"]["code"] == "LAB-1"
    assert client.get(f"{API}/{room['id']}", headers=admin).json()["children"][0]["code"] == "EQ-1"

    # equipment can't hold equipment; rooms can't be nested
    assert client.post(API, json=equip(code="e2", parent_id=eq.json()["id"]), headers=admin).status_code == 400
    assert client.post(API, json=lab(code="l2", parent_id=room["id"]), headers=admin).status_code == 400
    assert client.post(API, json=equip(code="e3", parent_id=999), headers=admin).status_code == 404
    # field rules
    assert client.post(API, json=equip(code="e4", capacity=5), headers=admin).status_code == 400
    assert client.post(API, json=lab(code="l3", serial_number="x"), headers=admin).status_code == 400
    # a room holding equipment can't be deleted until emptied
    assert client.delete(f"{API}/{room['id']}", headers=admin).status_code == 409
    assert client.delete(f"{API}/{eq.json()['id']}", headers=admin).status_code == 204
    assert client.delete(f"{API}/{room['id']}", headers=admin).status_code == 204


def test_move_equipment_between_rooms(client, staff):
    admin = auth_headers(client, "admin@x.com")
    a = client.post(API, json=lab(code="A"), headers=admin).json()["id"]
    b = client.post(API, json=lab(code="B"), headers=admin).json()["id"]
    e = client.post(API, json=equip(parent_id=a), headers=admin).json()["id"]
    assert client.patch(f"{API}/{e}", json={"parent_id": b}, headers=admin).json()["parent"]["code"] == "B"
    assert client.patch(f"{API}/{e}", json={"parent_id": None}, headers=admin).json()["parent"] is None
    assert client.patch(f"{API}/{e}", json={"parent_id": e}, headers=admin).status_code == 400


def test_validation_and_uniqueness(client, staff):
    admin = auth_headers(client, "admin@x.com")
    assert client.post(API, json=lab(), headers=admin).status_code == 201
    assert client.post(API, json=lab(name="Other", code="LAB-1"), headers=admin).status_code == 409  # case-insens.
    assert client.post(API, json=lab(code="x", name=""), headers=admin).status_code == 422
    assert client.post(API, json=lab(code="y", kind="spaceship"), headers=admin).status_code == 422
    assert client.post(API, json=lab(code="z", capacity=0), headers=admin).status_code == 422


def test_status_changes_and_search(client, staff):
    admin = auth_headers(client, "admin@x.com")
    room = client.post(API, json=lab(), headers=admin).json()["id"]
    e1 = client.post(API, json=equip(code="PC-1", name="Dell PC", serial_number="D1", parent_id=room), headers=admin).json()["id"]
    client.post(API, json=equip(code="PC-2", name="Dell PC", serial_number="D2", parent_id=room), headers=admin)
    client.post(API, json=equip(code="CAM", name="Camera", serial_number="C1"), headers=admin)
    labs = auth_headers(client, "lab@x.com")   # lab staff may update equipment status
    assert client.patch(f"{API}/{e1}", json={"status": "maintenance"}, headers=labs).json()["status"] == "maintenance"
    assert client.patch(f"{API}/{e1}", json={"status": "broken"}, headers=labs).status_code == 422

    s = auth_headers(client, "stud@x.com")
    codes = lambda **p: {r["code"] for r in client.get(API, params=p, headers=s).json()}
    assert codes() == {"LAB-1", "PC-1", "PC-2", "CAM"}
    assert codes(kind="equipment") == {"PC-1", "PC-2", "CAM"}
    assert codes(status="maintenance") == {"PC-1"}
    assert codes(q="dell") == {"PC-1", "PC-2"}
    assert codes(q="C1") == {"CAM"}
    assert codes(parent_id=room) == {"PC-1", "PC-2"}
    assert client.get(API, params={"kind": "x"}, headers=s).status_code == 422


def test_department_and_tree(client, staff):
    admin = auth_headers(client, "admin@x.com")
    hod = auth_headers(client, "hod@x.com")
    room = client.post(API, json=lab(), headers=admin).json()["id"]
    client.post(API, json=equip(parent_id=room), headers=admin)
    client.post(API, json=equip(code="SHARED", name="Laptop", serial_number="L"), headers=admin)

    dept = "/api/v1/department"
    assert client.put(dept, json={"name": "Computer Science", "code": "cs"}, headers=admin).status_code == 403
    r = client.put(dept, json={"name": "Computer Science", "code": "cs"}, headers=hod)
    assert r.status_code == 200 and r.json()["code"] == "CS"

    tree = client.get(f"{dept}/tree", headers=auth_headers(client, "stud@x.com")).json()
    assert tree["name"] == "Computer Science"
    by_code = {c["code"]: c for c in tree["children"]}
    assert set(by_code) == {"LAB-1", "SHARED"}                       # rooms/labs + unassigned equipment
    assert by_code["LAB-1"]["children"][0]["code"] == "EQ-1"          # equipment nested in the lab
    assert client.get(f"{dept}/tree").status_code == 401
