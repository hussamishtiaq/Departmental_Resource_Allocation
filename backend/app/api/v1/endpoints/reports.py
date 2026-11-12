from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.dependencies.auth import require_permission
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.report import MonitorOverview
from app.services import report_service

router = APIRouter(prefix="/monitor", tags=["monitoring"])


@router.get("", response_model=MonitorOverview)
def monitor(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.RESERVATIONS_REVIEW)),
):
    """Who is using which resource right now, what starts soon, what awaits approval."""
    return report_service.monitor_overview(db)
