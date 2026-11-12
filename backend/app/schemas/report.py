from datetime import datetime

from pydantic import BaseModel

from app.schemas.reservation import ReservationRead


class MonitorSummary(BaseModel):
    total_resources: int
    available: int
    maintenance: int
    damaged: int
    retired: int
    in_use_now: int
    pending_requests: int
    starting_next_24h: int


class MonitorOverview(BaseModel):
    generated_at: datetime
    summary: MonitorSummary
    in_use_now: list[ReservationRead]       # approved bookings running right now
    upcoming: list[ReservationRead]         # approved, starting within 24 hours
    pending: list[ReservationRead]          # waiting for approval (oldest first)
    needs_attention: list[dict]             # resources in maintenance / damaged
