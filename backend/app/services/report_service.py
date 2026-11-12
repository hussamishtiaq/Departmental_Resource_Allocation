from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.models.resource import Resource


def monitor_overview(db: Session) -> dict:
    """Live picture of resource usage for staff."""
    now = datetime.now(timezone.utc)
    soon = now + timedelta(hours=24)

    by_status = dict(db.execute(select(Resource.status, func.count()).group_by(Resource.status)).all())
    in_use = list(db.scalars(
        select(Reservation).where(
            Reservation.status == "approved", Reservation.start_time <= now, Reservation.end_time > now
        ).order_by(Reservation.end_time)))
    upcoming = list(db.scalars(
        select(Reservation).where(
            Reservation.status == "approved", Reservation.start_time > now, Reservation.start_time <= soon
        ).order_by(Reservation.start_time)))
    pending = list(db.scalars(
        select(Reservation).where(Reservation.status == "pending", Reservation.end_time > now)
        .order_by(Reservation.created_at)))
    attention = [
        {"id": r.id, "name": r.name, "code": r.code, "kind": r.kind, "status": r.status}
        for r in db.scalars(select(Resource).where(Resource.status.in_(["maintenance", "damaged"])).order_by(Resource.name))
    ]
    return {
        "generated_at": now,
        "summary": {
            "total_resources": sum(by_status.values()),
            "available": by_status.get("available", 0),
            "maintenance": by_status.get("maintenance", 0),
            "damaged": by_status.get("damaged", 0),
            "retired": by_status.get("retired", 0),
            "in_use_now": len(in_use),
            "pending_requests": len(pending),
            "starting_next_24h": len(upcoming),
        },
        "in_use_now": in_use,
        "upcoming": upcoming,
        "pending": pending,
        "needs_attention": attention,
    }
