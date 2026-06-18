from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request # Added Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app import crud, database, security, schemas, auth
from app.config import settings
from app.redis_client import blacklist_token

# Import the limiter from your main app file to avoid circular imports
from app.utils import limiter 

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute") # Day 6: Added Rate Limit (5 tries per minute)
def login(
    request: Request, # Day 6: Required for Rate Limiting
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(database.get_db)
):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Issue both Access and Refresh tokens
    access_token = security.create_access_token(data={"sub": str(user.id)})
    refresh_token = security.create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=schemas.Token)
def refresh(refresh_token: str):
    """Exchanges a 7-day Refresh Token for a new set of tokens."""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        new_access = security.create_access_token(data={"sub": user_id})
        new_refresh = security.create_refresh_token(data={"sub": user_id})
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
def logout(token: str = Depends(auth.oauth2_scheme), current_user = Depends(auth.get_current_user)):
    """Day 5: Adds the current token to the Redis blacklist."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        
        # Calculate time remaining until token naturally expires
        remaining = exp - int(datetime.utcnow().timestamp())
        
        if remaining > 0:
            blacklist_token(token, remaining)
            
        return {"message": "Successfully logged out"}
    except Exception:
        raise HTTPException(status_code=400, detail="Could not process logout")