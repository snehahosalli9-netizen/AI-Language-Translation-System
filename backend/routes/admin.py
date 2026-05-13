"""Admin routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.database import get_db
from database.schemas import User, Language, LanguagePair
from services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin")


class UserAdminResponse(BaseModel):
    """User admin response model."""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True


class LanguageRequest(BaseModel):
    """Language creation request."""
    code: str
    name: str
    native_name: Optional[str] = None


# Initialize auth service
auth_service = AuthService()


async def verify_admin(current_user: User = Depends(auth_service.get_current_user)):
    """Verify that current user is admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/users", response_model=List[UserAdminResponse])
async def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """
    List all users (admin only).
    """
    try:
        users = db.query(User).all()
        return [UserAdminResponse.from_orm(u) for u in users]
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.post("/users/{user_id}/ban", status_code=status.HTTP_200_OK)
async def ban_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """
    Ban a user (admin only).
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        db.commit()
        
        logger.warning(f"User banned by admin {admin.id}: user_id={user_id}")
        
        return {"message": f"User {user.email} has been banned"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error banning user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user"
        )


@router.get("/languages")
async def list_languages(
    db: Session = Depends(get_db)
):
    """
    List all available languages.
    """
    try:
        languages = db.query(Language).filter(Language.is_active == True).all()
        return [
            {
                "code": lang.code,
                "name": lang.name,
                "native_name": lang.native_name
            } for lang in languages
        ]
    except Exception as e:
        logger.error(f"Error fetching languages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch languages"
        )


@router.post("/languages", status_code=status.HTTP_201_CREATED)
async def add_language(
    request: LanguageRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """
    Add a new language (admin only).
    """
    try:
        # Check if language already exists
        existing = db.query(Language).filter(Language.code == request.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Language already exists"
            )
        
        language = Language(
            code=request.code,
            name=request.name,
            native_name=request.native_name
        )
        
        db.add(language)
        db.commit()
        db.refresh(language)
        
        logger.info(f"New language added by admin {admin.id}: {request.code}")
        
        return {
            "message": "Language added successfully",
            "code": language.code,
            "name": language.name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding language: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add language"
        )
