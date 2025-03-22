from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
  email: EmailStr
  password: str
  name: str
  gender: str
  age: int
