"""Fill the database with demo data (safe to re-run):

    python -m app.db.seed_demo

Creates one user per role (password: Password123) and a sample department with
rooms, laboratories and equipment arranged as Department -> Room/Lab -> Equipment.
"""
from datetime import datetime, timedelta, timezone

from app.core.permissions import RoleName
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.reservation import Reservation
from app.models.resource import Resource
from app.models.user import User
from app.repositories import resource_repository as resources
from app.repositories import user_repository as users
from app.services.auth_service import seed_roles
from app.services.department_service import get_or_create_department

PASSWORD = "Password123"

DEMO_USERS = [
    ("Dr. Ahmed Raza", "hod@demo.com", RoleName.HOD),
    ("Sara Malik", "admin@demo.com", RoleName.DEPARTMENT_ADMIN),
    ("Bilal Hussain", "labstaff@demo.com", RoleName.LAB_STAFF),
    ("Dr. Ayesha Khan", "faculty@demo.com", RoleName.FACULTY),
    ("Usman Ali", "student@demo.com", RoleName.STUDENT),
]

# (code, kind, name, location, capacity, children: (code, name, serial, status))
DEMO_RESOURCES = [
    ("R-101", "room", "Lecture Room 101", "Block A, Ground Floor", 60, []),
    ("R-102", "room", "Seminar Room", "Block A, First Floor", 30, [
        ("EQ-PRJ-01", "Projector (Epson EB-X06)", "EPX06-1001", "available"),
    ]),
    ("LAB-CS1", "laboratory", "Computer Lab 1", "Block B, Room 1", 40, [
        ("EQ-PC-01", "Desktop PC Dell OptiPlex", "DL-77120", "available"),
        ("EQ-PC-02", "Desktop PC Dell OptiPlex", "DL-77121", "available"),
        ("EQ-PC-03", "Desktop PC Dell OptiPlex", "DL-77122", "maintenance"),
    ]),
    ("LAB-NET", "laboratory", "Networking Lab", "Block B, Room 4", 25, [
        ("EQ-RTR-01", "Cisco Router 2901", "CS-2901-A", "available"),
        ("EQ-SW-01", "Cisco Switch 2960", "CS-2960-B", "damaged"),
    ]),
    ("LAB-ELEC", "laboratory", "Electronics Lab", "Block C, Room 2", 30, [
        ("EQ-OSC-01", "Digital Oscilloscope", "OSC-5543", "available"),
    ]),
]
# shared (unassigned) equipment
DEMO_SHARED = [
    ("EQ-LAP-01", "Laptop Lenovo ThinkPad", "LN-33001", "available"),
    ("EQ-CAM-01", "Digital Camera Canon", "CN-90817", "available"),
]


def _equipment(db, parent_id, code, name, serial, status):
    if resources.code_exists(db, code):
        return
    db.add(Resource(kind="equipment", code=code, name=name, serial_number=serial,
                    status=status, parent_id=parent_id))
    db.commit()


def _demo_reservations(db) -> None:
    """A few bookings around 'now' so the monitor page has something to show."""
    if db.query(Reservation).filter(Reservation.purpose.like("[demo]%")).first():
        return
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    by_email = {u: users.get_by_email(db, u) for _, u, _ in DEMO_USERS}
    by_code = {r.code: r for r in db.query(Resource).all()}
    hod, adm = by_email["hod@demo.com"], by_email["admin@demo.com"]
    # (resource, user, start offset h, length h, status, purpose)
    plan = [
        ("LAB-CS1", "faculty@demo.com", -1, 3, "approved", "[demo] Programming lab class"),
        ("EQ-PRJ-01", "faculty@demo.com", 4, 2, "approved", "[demo] Seminar presentation"),
        ("LAB-NET", "student@demo.com", 26, 2, "approved", "[demo] Networking practice"),
        ("LAB-ELEC", "student@demo.com", 30, 2, "pending", "[demo] Circuit project work"),
        ("EQ-OSC-01", "student@demo.com", 6, 1, "pending", "[demo] Measure signals"),
    ]
    for code, email, offset, length, status, purpose in plan:
        start = now + timedelta(hours=offset)
        approved = status == "approved"
        db.add(Reservation(
            resource_id=by_code[code].id, user_id=by_email[email].id, start_time=start,
            end_time=start + timedelta(hours=length), purpose=purpose, status=status,
            created_by_id=by_email[email].id,
            reviewed_by_id=adm.id if approved else None,
            reviewed_at=datetime.now(timezone.utc) if approved else None,
        ))
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed_roles(db)
        dept = get_or_create_department(db)
        dept.name, dept.code = "Department of Computer Science", "CS"
        dept.description = "Demo department"
        db.commit()

        for full_name, email, role in DEMO_USERS:
            if not users.get_by_email(db, email):
                db.add(User(full_name=full_name, email=email,
                            hashed_password=hash_password(PASSWORD),
                            role_id=users.get_role_by_name(db, role).id))
        db.commit()

        for code, kind, name, location, capacity, kids in DEMO_RESOURCES:
            if not resources.code_exists(db, code):
                db.add(Resource(kind=kind, code=code, name=name,
                                location=location, capacity=capacity))
                db.commit()
            parent = db.query(Resource).filter_by(code=code).one()
            for kid in kids:
                _equipment(db, parent.id, *kid)
        for item in DEMO_SHARED:
            _equipment(db, None, *item)
        _demo_reservations(db)
    print("Demo data ready. Log in with hod@demo.com / admin@demo.com / "
          f"labstaff@demo.com / faculty@demo.com / student@demo.com  (password: {PASSWORD})")


if __name__ == "__main__":
    main()
