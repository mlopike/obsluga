from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str
    email: str
    department: str
    role: str
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
    department: str


class TokenOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str
    profile: ProfileOut
