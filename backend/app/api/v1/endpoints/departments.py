from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.dependencies.auth import require_permission
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.department import DepartmentRead, DepartmentTree, DepartmentUpdate
from app.services import department_service as svc

router = APIRouter(prefix="/department", tags=["department"])


@router.get("", response_model=DepartmentRead)
def get_department(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.RESOURCES_READ)),
):
    """The single department managed by the system."""
    return svc.get_or_create_department(db)


@router.put("", response_model=DepartmentRead)
def update_department(
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.DEPARTMENT_MANAGE)),
):
    """Rename the department / edit its details. HOD only."""
    dept = svc.get_or_create_department(db)
    for key, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(dept, key, value.upper() if key == "code" else value)
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/tree", response_model=DepartmentTree)
def department_tree(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.RESOURCES_READ)),
):
    """Department -> rooms/laboratories -> equipment, as nested JSON."""
    return svc.build_tree(db)
