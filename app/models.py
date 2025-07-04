from datetime import UTC, datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class FamilyMember(SQLModel, table=True):
    __tablename__ = "family_members"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(max_length=100, nullable=False, unique=True)
    created_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationship to ratings
    ratings: List["GameRating"] = Relationship(
        back_populates="family_member",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    def __repr__(self):
        return f"<FamilyMember(id={self.id}, name='{self.name}')>"


class Game(SQLModel, table=True):
    __tablename__ = "games"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=255, nullable=False, index=True)
    player_count: Optional[str] = Field(max_length=100, nullable=True)
    game_type: Optional[str] = Field(max_length=100, nullable=True)
    playtime: Optional[str] = Field(max_length=100, nullable=True)
    complexity: Optional[str] = Field(max_length=100, nullable=True)
    description: Optional[str] = Field(nullable=True)
    created_at: Optional[datetime] = Field(default=None, nullable=True)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationship to family member ratings
    family_ratings: List["GameRating"] = Relationship(
        back_populates="game", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def average_rating(self) -> Optional[float]:
        """Calculate the average rating from all family members for this game."""
        if not self.family_ratings:
            return None

        total_rating = sum(rating.rating for rating in self.family_ratings)
        return round(total_rating / len(self.family_ratings), 1)

    def __repr__(self):
        return f"<Game(id={self.id}, title='{self.title}')>"


class GameRating(SQLModel, table=True):
    __tablename__ = "game_ratings"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    game_id: int = Field(foreign_key="games.id", nullable=False)
    family_member_id: int = Field(foreign_key="family_members.id", nullable=False)
    rating: int = Field(nullable=False)  # 1-10 rating
    created_at: Optional[datetime] = Field(default=None, nullable=True)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationships
    game: Optional[Game] = Relationship(back_populates="family_ratings")
    family_member: Optional[FamilyMember] = Relationship(back_populates="ratings")

    def __repr__(self):
        return f"<GameRating(game_id={self.game_id}, family_member_id={self.family_member_id}, rating={self.rating})>"
