"""SQLAlchemy database models/schemas."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    translations = relationship("Translation", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Translation(Base):
    """Translation record model."""
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    bleu_score = Column(Float, default=0.0, nullable=False)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="translations")
    favorites = relationship("Favorite", back_populates="translation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Translation(id={self.id}, {self.source_language}->{self.target_language})>"


class Favorite(Base):
    """Favorite translation model."""
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    translation_id = Column(Integer, ForeignKey("translations.id", ondelete="CASCADE"), nullable=False, index=True)
    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    translation = relationship("Translation", back_populates="favorites")
    
    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, translation_id={self.translation_id})>"


class Feedback(Base):
    """User feedback model."""
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    translation_id = Column(Integer, ForeignKey("translations.id"), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<Feedback(user_id={self.user_id}, rating={self.rating})>"


class Language(Base):
    """Supported languages model."""
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    native_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Language(code={self.code}, name={self.name})>"


class LanguagePair(Base):
    """Supported language translation pairs."""
    __tablename__ = "language_pairs"
    
    id = Column(Integer, primary_key=True, index=True)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    model_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<LanguagePair({self.source_language}->{self.target_language})>"


class TranslationModel(Base):
    """Machine learning models information."""
    __tablename__ = "translation_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    model_id = Column(String(255), nullable=False)  # Hugging Face model ID
    version = Column(String(50), nullable=False)
    language_pairs = Column(Integer, nullable=False)
    average_bleu_score = Column(Float, nullable=True)
    model_size_mb = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<TranslationModel(name={self.name})>"
