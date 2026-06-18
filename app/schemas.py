from pydantic import BaseModel, EmailStr, field_validator # Use field_validator for Pydantic v2

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        # Check password length 
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Check for uppercase letter 
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

    @field_validator("username")
    @classmethod
    def username_clean(cls, v: str) -> str:
        # Check username length 
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v.lower().strip()
    
class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str | None = None