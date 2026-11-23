# Import every model so that Base.metadata knows about all tables.
from app.models.reservation import Reservationss
from app.models.department import Department
from app.models.reservation import Reservation
from app.models.resource import Resource
from app.models.role import Role
from app.models.user import User

__all__ = ["Department", "Reservation", "Resource", "Role", "User"]




