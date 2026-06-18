from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import models, schemas

# FIXED: Added bcrypt__ident="2b" to bypass the library version bug
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto", 
    bcrypt__ident="2b" 
)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, user: schemas.UserCreate):
    # Hash the password using the fixed context
    hashed_password = pwd_context.hash(user.password)
    
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_pw=hashed_password,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user