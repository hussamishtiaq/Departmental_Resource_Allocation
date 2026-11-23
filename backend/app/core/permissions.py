from enum import Enum


class RoleName(str, Enum):
    HOD = "hod"
    DEPARTMENT_ADMIN = "department_admin"
    LAB_STAFF = "lab_staff"
    FACULTY = "faculty"
    STUDENT = "student"


class Permission(str, Enum):
    # Reservation permissions
    RESERVATIONS_CREATE = "reservations:create"
    RESERVATIONS_REVIEW = "reservations:review"
    RESERVATIONS_ASSIGN = "reservations:assign"


role_permissions = {
    RoleName.HOD: {
        Permission.RESERVATIONS_CREATE,
        Permission.RESERVATIONS_REVIEW,
        Permission.RESERVATIONS_ASSIGN,
    },

    RoleName.DEPARTMENT_ADMIN: {
        Permission.RESERVATIONS_CREATE,
        Permission.RESERVATIONS_REVIEW,
        Permission.RESERVATIONS_ASSIGN,
    },

    RoleName.LAB_STAFF: {
        Permission.RESERVATIONS_CREATE,
        Permission.RESERVATIONS_REVIEW,
    },

    RoleName.FACULTY: {
        Permission.RESERVATIONS_CREATE,
    },

    RoleName.STUDENT: {
        Permission.RESERVATIONS_CREATE,
    },
}


def has_permission(role: RoleName, permission: Permission) -> bool:
    return permission in role_permissions.get(role, set())