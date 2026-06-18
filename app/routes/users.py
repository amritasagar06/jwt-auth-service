from fastapi import APIRouter, Depends
from app import schemas, auth, models

router = APIRouter()

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    If this returns your data, your authorization is working perfectly!
    """
    return current_user