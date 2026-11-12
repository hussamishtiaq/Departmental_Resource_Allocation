from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.resource import Resource


def get_or_create_department(db: Session) -> Department:
    """The system manages exactly one department; create a placeholder on first use."""
    dept = db.query(Department).order_by(Department.id).first()
    if dept is None:
        dept = Department(name="Department", code="DEPT")
        db.add(dept)
        db.commit()
        db.refresh(dept)
    return dept


def _node(r: Resource) -> dict:
    return {
        "id": r.id, "kind": r.kind, "name": r.name, "code": r.code,
        "status": r.status, "capacity": r.capacity, "children": [],
    }


def build_tree(db: Session) -> dict:
    """Department -> rooms/laboratories -> equipment (+ unassigned equipment)."""
    dept = get_or_create_department(db)
    resources = db.query(Resource).order_by(Resource.name).all()
    nodes = {r.id: _node(r) for r in resources}
    roots = []
    for r in resources:
        if r.parent_id in nodes:
            nodes[r.parent_id]["children"].append(nodes[r.id])
        else:
            roots.append(nodes[r.id])
    return {
        "id": dept.id, "name": dept.name, "code": dept.code,
        "description": dept.description, "children": roots,
    }
