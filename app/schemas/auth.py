from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterIn(BaseModel):
    """Регистрация всегда создаёт сотрудника. Роль инженера назначает администратор."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    department: str
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_has_digit(cls, value: str) -> str:
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return value


class LoginIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: str
    password: str
    remember: bool = False


class ProfileOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    full_name: str
    role: str
    perm: int
    department: str


class TokenOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str
    profile: ProfileOut


class DepartmentOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str


class UserOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    full_name: str
    email: str
    role: str
    perm: int
    department: str


class UserRolePatch(BaseModel):
    role: str
