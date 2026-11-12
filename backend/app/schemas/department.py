from pydantic import BaseModel, ConfigDict, Field


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    code: str | None = Field(default=None, min_length=2, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = Field(default=None, max_length=500)


class TreeNode(BaseModel):
    id: int
    kind: str
    name: str
    code: str
    status: str
    capacity: int | None = None
    children: list["TreeNode"] = []


class DepartmentTree(DepartmentRead):
    """Root of the hierarchy: the department and everything below it."""
    children: list[TreeNode] = []
