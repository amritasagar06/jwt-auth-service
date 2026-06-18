from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app import database, models
from app.config import settings
from app.redis_client import is_token_blacklisted

# This tells FastAPI to look for the "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    """
    The core security function. It checks:
    1. Is the token blacklisted in Redis?
    2. Is the signature valid?
    3. Is it an 'access' token (not a refresh token)?
    4. Does the user exist in the DB?
    """
    # Step 1: Redis Blacklist Check (Day 5)
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Step 2: Decode and verify signature
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        # Step 3: Type Check (Day 4)
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Please use an access token.",
            )
            
        if user_id is None:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
        
    # Step 4: Database Check
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user