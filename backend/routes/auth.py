"""Authentication routes."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from database.database import get_db
from database.schemas import User
from services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")


# Pydantic models for request/response
class SignupRequest(BaseModel):
    """User registration request model."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }


class LoginRequest(BaseModel):
    """User login request model."""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    full_name: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# Initialize auth service
auth_service = AuthService()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **email**: User's email address (must be unique)
    - **password**: Password (minimum 8 characters)
    - **full_name**: User's full name
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            logger.warning(f"Signup attempt with existing email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Create new user
        password_hash = auth_service.hash_password(request.password)
        new_user = User(
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate tokens
        access_token = auth_service.create_access_token(str(new_user.id))
        
        logger.info(f"New user registered: {request.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint.
    
    Returns JWT access token for authenticated requests.
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user or not auth_service.verify_password(request.password, user.password_hash):
            logger.warning(f"Failed login attempt for email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Generate tokens
        access_token = auth_service.create_access_token(str(user.id))
        
        logger.info(f"User logged in: {request.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(auth_service.get_current_user)):
    """
    Get current user's profile information.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse.from_orm(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(auth_service.get_current_user)):
    """
    Logout current user.
    
    On client side, remove the stored JWT token.
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}
