"""Analytics and statistics routes."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.database import get_db
from database.schemas import User, Translation
from services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics")


# Initialize auth service
auth_service = AuthService()


@router.get("/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get dashboard statistics for current user.
    """
    try:
        # Get total translations
        total_translations = db.query(func.count(Translation.id)).filter(
            Translation.user_id == current_user.id
        ).scalar()
        
        # Get translations in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_translations = db.query(func.count(Translation.id)).filter(
            Translation.user_id == current_user.id,
            Translation.created_at >= seven_days_ago
        ).scalar()
        
        # Get average BLEU score
        avg_bleu = db.query(func.avg(Translation.bleu_score)).filter(
            Translation.user_id == current_user.id
        ).scalar() or 0
        
        # Get language pairs used
        language_pairs = db.query(
            Translation.source_language,
            Translation.target_language,
            func.count(Translation.id).label('count')
        ).filter(
            Translation.user_id == current_user.id
        ).group_by(
            Translation.source_language,
            Translation.target_language
        ).all()
        
        return {
            "total_translations": total_translations,
            "recent_translations": recent_translations,
            "average_bleu_score": float(avg_bleu),
            "language_pairs": [
                {
                    "source": pair[0],
                    "target": pair[1],
                    "count": pair[2]
                } for pair in language_pairs
            ]
        }
    
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )


@router.get("/statistics")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
    days: int = Query(30, ge=1, le=365)
):
    """
    Get detailed statistics for specified period.
    
    - **days**: Number of days to analyze (default: 30)
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        translations = db.query(Translation).filter(
            Translation.user_id == current_user.id,
            Translation.created_at >= cutoff_date
        ).all()
        
        if not translations:
            return {
                "period_days": days,
                "total_translations": 0,
                "average_bleu_score": 0,
                "average_processing_time": 0,
                "statistics": {}
            }
        
        # Calculate statistics
        bleu_scores = [t.bleu_score for t in translations if t.bleu_score]
        processing_times = [t.processing_time for t in translations if t.processing_time]
        
        avg_bleu = sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "period_days": days,
            "total_translations": len(translations),
            "average_bleu_score": avg_bleu,
            "average_processing_time": avg_time,
            "min_processing_time": min(processing_times) if processing_times else 0,
            "max_processing_time": max(processing_times) if processing_times else 0
        }
    
    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )
