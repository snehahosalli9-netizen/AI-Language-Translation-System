"""Favorites routes."""

import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.database import get_db
from database.schemas import User, Translation, Favorite
from services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/favorites")


class FavoriteResponse(BaseModel):
    """Favorite response model."""
    id: int
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Initialize auth service
auth_service = AuthService()


@router.get("", response_model=List[FavoriteResponse])
async def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get all favorite translations for current user.
    """
    try:
        favorites = db.query(Favorite).filter(
            Favorite.user_id == current_user.id
        ).all()
        
        result = []
        for fav in favorites:
            translation = fav.translation
            result.append(FavoriteResponse(
                id=fav.id,
                source_text=translation.source_text,
                translated_text=translation.translated_text,
                source_language=translation.source_language,
                target_language=translation.target_language,
                created_at=translation.created_at
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching favorites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch favorites"
        )


@router.post("/{translation_id}", status_code=status.HTTP_201_CREATED)
async def save_as_favorite(
    translation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Save a translation as favorite.
    """
    try:
        # Check if translation exists and belongs to user
        translation = db.query(Translation).filter(
            Translation.id == translation_id,
            Translation.user_id == current_user.id
        ).first()
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found"
            )
        
        # Check if already favorited
        existing_favorite = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.translation_id == translation_id
        ).first()
        
        if existing_favorite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Translation already favorited"
            )
        
        # Create favorite
        favorite = Favorite(
            user_id=current_user.id,
            translation_id=translation_id
        )
        
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        
        logger.info(f"Favorite saved: user={current_user.id}, translation={translation_id}")
        
        return {"message": "Translation saved as favorite", "id": favorite.id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving favorite: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save favorite"
        )


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Remove a translation from favorites.
    """
    try:
        favorite = db.query(Favorite).filter(
            Favorite.id == favorite_id,
            Favorite.user_id == current_user.id
        ).first()
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        db.delete(favorite)
        db.commit()
        
        logger.info(f"Favorite removed: user={current_user.id}, favorite={favorite_id}")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove favorite"
        )
