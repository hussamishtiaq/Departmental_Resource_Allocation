"""Bootstrap the first user (the Head of Department):

    python -m app.db.create_admin "Full Name" hod@example.com 'Password123'
"""
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories import user_repository as users
from app.services.auth_service import seed_roles


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    full_name, email, password = sys.argv[1:]
    with SessionLocal() as db:
        seed_roles(db)
        if users.get_by_email(db, email):
            sys.exit("A user with that email already exists")
        role = users.get_role_by_name(db, "hod")
        db.add(User(full_name=full_name, email=email.lower(),
                    hashed_password=hash_password(password), role_id=role.id))
        db.commit()
    print(f"HOD {email} created")


if __name__ == "__main__":
    main()
