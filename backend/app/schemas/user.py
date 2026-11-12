from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, computed_field

from app.core.permissions import assignable_roles, permissions_for


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    level: int


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    role: RoleRead
    created_at: datetime

    @computed_field
    @property
    def permissions(self) -> list[str]:
        return permissions_for(self.role.name)

    @computed_field
    @property
    def assignable_roles(self) -> list[str]:
        """Roles this user is allowed to hand out to others."""
        return assignable_roles(self.role.name)


class UserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
