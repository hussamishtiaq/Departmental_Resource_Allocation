"""Role hierarchy and permission matrix (the authorization rules live here).

Authority chain (higher level outranks lower):
HOD > department administrator (resource coordinator) > laboratory staff
> faculty > student.
"""
from app.utils.enums import StrEnum


class RoleName(StrEnum):
    HOD = "hod"
    DEPARTMENT_ADMIN = "department_admin"
    LAB_STAFF = "lab_staff"
    FACULTY = "faculty"
    STUDENT = "student"


# (name, level, description)
ROLE_DEFINITIONS: list[tuple[str, int, str]] = [
    (RoleName.HOD, 100, "Head of Department - oversight of everything"),
    (RoleName.DEPARTMENT_ADMIN, 80, "Department administrator / resource coordinator"),
    (RoleName.LAB_STAFF, 60, "Laboratory staff - equipment, returns, maintenance"),
    (RoleName.FACULTY, 40, "Faculty member"),
    (RoleName.STUDENT, 20, "Student"),
]
ROLE_LEVELS: dict[str, int] = {name: level for name, level, _ in ROLE_DEFINITIONS}

DEFAULT_REGISTRATION_ROLE = RoleName.STUDENT


class Permission(StrEnum):
    USERS_READ = "users:read"
    USERS_MANAGE = "users:manage"
    DEPARTMENT_MANAGE = "department:manage"
    RESOURCES_READ = "resources:read"
    RESOURCES_MANAGE = "resources:manage"
    RESERVATIONS_CREATE = "reservations:create"  # request a resource for yourself
    RESERVATIONS_REVIEW = "reservations:review"  # approve / reject / cancel requests
    RESERVATIONS_ASSIGN = "reservations:assign"  # allocate a resource to a user directly


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    RoleName.HOD: set(Permission),
    RoleName.DEPARTMENT_ADMIN: {
        Permission.USERS_READ,
        Permission.USERS_MANAGE,
        Permission.RESOURCES_READ,
        Permission.RESOURCES_MANAGE,
        Permission.RESERVATIONS_CREATE,
        Permission.RESERVATIONS_REVIEW,
        Permission.RESERVATIONS_ASSIGN,
    },
    # Lab staff may manage / review equipment only (enforced in the services).
    RoleName.LAB_STAFF: {
        Permission.RESOURCES_READ,
        Permission.RESOURCES_MANAGE,
        Permission.RESERVATIONS_CREATE,
        Permission.RESERVATIONS_REVIEW,
    },
    RoleName.FACULTY: {Permission.RESOURCES_READ, Permission.RESERVATIONS_CREATE},
    RoleName.STUDENT: {Permission.RESOURCES_READ, Permission.RESERVATIONS_CREATE},
}


def has_permission(role_name: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role_name, set())


def permissions_for(role_name: str) -> list[str]:
    return sorted(p.value for p in ROLE_PERMISSIONS.get(role_name, set()))


def can_assign_role(actor_role: str, target_current_role: str, new_role: str) -> bool:
    """Hierarchy rule for changing someone's role.

    The HOD may assign any role. Everyone else may only touch users strictly
    below them and may only hand out roles strictly below their own level."""
    if actor_role == RoleName.HOD:
        return True
    actor = ROLE_LEVELS.get(actor_role, 0)
    return ROLE_LEVELS.get(target_current_role, 0) < actor and ROLE_LEVELS.get(new_role, 0) < actor


def assignable_roles(actor_role: str) -> list[str]:
    if actor_role == RoleName.HOD:
        return [n for n, _, _ in ROLE_DEFINITIONS]
    actor = ROLE_LEVELS.get(actor_role, 0)
    return [n for n, lvl, _ in ROLE_DEFINITIONS if lvl < actor]
