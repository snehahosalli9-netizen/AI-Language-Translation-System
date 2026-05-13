"""Translation routes."""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.database import get_db
from database.schemas import User, Translation, Language
from services.auth_service import AuthService
from services.translation_service import TranslationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/translate")


# Pydantic models
class TranslationRequest(BaseModel):
    """Text translation request model."""
    text: str = Field(..., min_length=1, max_length=5000)
    source_language: str = Field(..., min_length=2, max_length=10)
    target_language: str = Field(..., min_length=2, max_length=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, how are you?",
                "source_language": "en",
                "target_language": "hi"
            }
        }


class TranslationResponse(BaseModel):
    """Translation response model."""
    id: int
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    bleu_score: float
    processing_time: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LanguageDetectionResponse(BaseModel):
    """Language detection response."""
    detected_language: str
    language_name: str
    confidence: float


# Initialize services
auth_service = AuthService()
translation_service = TranslationService()


@router.post("/text", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Translate text from source to target language.
    
    - **text**: Text to translate (max 5000 characters)
    - **source_language**: Source language code (e.g., 'en')
    - **target_language**: Target language code (e.g., 'hi')
    
    Returns translation with BLEU score and confidence.
    """
    try:
        # Validate languages
        if request.source_language == request.target_language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target languages cannot be the same"
            )
        
        # Perform translation
        import time
        start_time = time.time()
        
        translated_text, confidence, bleu_score = translation_service.translate(
            request.text,
            request.source_language,
            request.target_language
        )
        
        processing_time = time.time() - start_time
        
        # Save to database
        translation = Translation(
            user_id=current_user.id,
            source_text=request.text,
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language,
            confidence=confidence,
            bleu_score=bleu_score,
            processing_time=processing_time
        )
        
        db.add(translation)
        db.commit()
        db.refresh(translation)
        
        logger.info(f"Translation completed for user {current_user.id}: {request.source_language}->{request.target_language}")
        
        return TranslationResponse.from_orm(translation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation failed"
        )


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(
    text: str = Field(..., min_length=1, max_length=5000)
):
    """
    Detect the language of input text.
    
    Uses XLM-RoBERTa model for language detection.
    """
    try:
        detected_lang, language_name, confidence = translation_service.detect_language(text)
        
        return LanguageDetectionResponse(
            detected_language=detected_lang,
            language_name=language_name,
            confidence=confidence
        )
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Language detection failed"
        )


@router.get("/languages")
async def get_supported_languages(db: Session = Depends(get_db)):
    """
    Get list of all supported languages.
    """
    try:
        languages = db.query(Language).filter(Language.is_active == True).all()
        return {
            "total": len(languages),
            "languages": [{
                "code": lang.code,
                "name": lang.name,
                "native_name": lang.native_name
            } for lang in languages]
        }
    except Exception as e:
        logger.error(f"Error fetching languages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch languages"
        )
