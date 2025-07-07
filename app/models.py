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
    game_type: Optional[str] = Field(
        max_length=500, nullable=True
    )  # Comma-separated list for database storage
    game_elements: Optional[str] = Field(
        max_length=500, nullable=True
    )  # Comma-separated list for database storage
    setup_time: Optional[str] = Field(max_length=100, nullable=True)
    playtime: Optional[str] = Field(max_length=100, nullable=True)
    complexity: Optional[str] = Field(max_length=100, nullable=True)
    description: Optional[str] = Field(nullable=True)
    created_at: Optional[datetime] = Field(default=None, nullable=True)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationship to family member ratings
    family_ratings: List["GameRating"] = Relationship(
        back_populates="game", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Relationship to play logs
    play_logs: List["PlayLog"] = Relationship(
        back_populates="game", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def average_rating(self) -> Optional[float]:
        """Calculate the average rating from all family members for this game."""
        if not self.family_ratings:
            return None

        total_rating = sum(rating.rating for rating in self.family_ratings)
        return round(total_rating / len(self.family_ratings), 1)

    @property
    def last_played(self) -> Optional[datetime]:
        """Get the most recent play date for this game."""
        if not self.play_logs:
            return None

        # Find the play log with the most recent played_date
        latest_play_log = max(self.play_logs, key=lambda log: log.played_date)
        return latest_play_log.played_date

    def __repr__(self):
        return f"<Game(id={self.id}, title='{self.title}')>"


class PlayLog(SQLModel, table=True):
    __tablename__ = "play_logs"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    game_id: int = Field(foreign_key="games.id", nullable=False)
    played_date: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )
    players: Optional[str] = Field(
        max_length=500, nullable=True
    )  # Comma-separated list of players
    notes: Optional[str] = Field(nullable=True)  # Optional notes about the play session
    duration_minutes: Optional[int] = Field(nullable=True)  # How long the game took
    winner: Optional[str] = Field(
        max_length=100, nullable=True
    )  # Who won (if applicable)
    created_at: Optional[datetime] = Field(default=None, nullable=True)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)

    # Relationships
    game: Optional[Game] = Relationship(back_populates="play_logs")

    def __repr__(self):
        return f"<PlayLog(game_id={self.game_id}, played_date='{self.played_date}')>"


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
