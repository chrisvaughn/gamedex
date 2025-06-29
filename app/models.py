from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationship to ratings
    ratings = relationship(
        "GameRating", back_populates="family_member", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FamilyMember(id={self.id}, name='{self.name}')>"


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    player_count = Column(String(100), nullable=True)
    game_type = Column(String(100), nullable=True)
    playtime = Column(String(100), nullable=True)
    complexity = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationship to family member ratings
    family_ratings = relationship(
        "GameRating", back_populates="game", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Game(id={self.id}, title='{self.title}')>"


class GameRating(Base):
    __tablename__ = "game_ratings"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-10 rating
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    game = relationship("Game", back_populates="family_ratings")
    family_member = relationship("FamilyMember", back_populates="ratings")

    def __repr__(self):
        return f"<GameRating(game_id={self.game_id}, family_member_id={self.family_member_id}, rating={self.rating})>"
