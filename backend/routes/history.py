"""Translation history routes."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.database import get_db
from database.schemas import User, Translation
from services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/history")


class HistoryItemResponse(BaseModel):
    """History item response model."""
    id: int
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    bleu_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# Initialize auth service
auth_service = AuthService()


@router.get("", response_model=List[HistoryItemResponse])
async def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    source_language: Optional[str] = None,
    target_language: Optional[str] = None
):
    """
    Get user's translation history.
    
    - **limit**: Number of records to return (default: 50, max: 500)
    - **offset**: Number of records to skip (for pagination)
    - **source_language**: Filter by source language code
    - **target_language**: Filter by target language code
    """
    try:
        query = db.query(Translation).filter(Translation.user_id == current_user.id)
        
        # Apply filters
        if source_language:
            query = query.filter(Translation.source_language == source_language)
        if target_language:
            query = query.filter(Translation.target_language == target_language)
        
        # Order by most recent first and apply pagination
        translations = query.order_by(Translation.created_at.desc()).offset(offset).limit(limit).all()
        
        return [HistoryItemResponse.from_orm(t) for t in translations]
    
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch history"
        )


@router.get("/{translation_id}", response_model=HistoryItemResponse)
async def get_history_item(
    translation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get a specific translation from history.
    """
    try:
        translation = db.query(Translation).filter(
            Translation.id == translation_id,
            Translation.user_id == current_user.id
        ).first()
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found"
            )
        
        return HistoryItemResponse.from_orm(translation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching translation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch translation"
        )


@router.delete("/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_item(
    translation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Delete a specific translation from history.
    """
    try:
        translation = db.query(Translation).filter(
            Translation.id == translation_id,
            Translation.user_id == current_user.id
        ).first()
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not found"
            )
        
        db.delete(translation)
        db.commit()
        
        logger.info(f"Translation deleted: {translation_id}")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting translation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete translation"
        )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Clear all translation history for current user.
    """
    try:
        db.query(Translation).filter(Translation.user_id == current_user.id).delete()
        db.commit()
        
        logger.info(f"History cleared for user: {current_user.id}")
        
        return None
    
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear history"
        )
