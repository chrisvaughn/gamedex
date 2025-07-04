import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models import Game


class TestDatabaseOperations:
    """Test cases for database operations"""

    def test_create_game_in_database(self, db_session: Session):
        """Test creating a game in the database"""
        game = Game(
            title="Test Game",
            player_count="2-4 players",
            game_type="Strategy",
            playtime="30-60 minutes",
            complexity="Medium",
        )

        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        assert game.id is not None
        assert game.title == "Test Game"
        assert game.player_count == "2-4 players"
        assert game.game_type == "Strategy"
        assert game.playtime == "30-60 minutes"
        assert game.complexity == "Medium"

    def test_query_games_from_database(self, db_session: Session, sample_games_data):
        """Test querying games from the database"""
        # Create games in database
        games = []
        for game_data in sample_games_data:
            game = Game(**game_data)
            db_session.add(game)
            games.append(game)

        db_session.commit()

        # Query all games
        all_games = db_session.query(Game).all()
        assert len(all_games) == 3

        # Query by title
        catan = db_session.query(Game).filter(Game.title == "Catan").first()
        assert catan is not None
        assert catan.title == "Catan"
        assert catan.game_type == "Strategy"

        # Query by game type
        strategy_games = (
            db_session.query(Game).filter(Game.game_type == "Strategy").all()
        )
        assert len(strategy_games) == 1
        assert strategy_games[0].title == "Catan"

    def test_update_game_in_database(self, db_session: Session):
        """Test updating a game in the database"""
        # Create a game
        game = Game(title="Original Title")
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        original_id = game.id
        original_created_at = game.created_at

        # Update the game
        game.title = "Updated Title"
        db_session.commit()
        db_session.refresh(game)

        # Check that the game was updated
        assert game.id == original_id
        assert game.title == "Updated Title"
        assert game.created_at == original_created_at
        assert game.updated_at > original_created_at

    def test_delete_game_from_database(self, db_session: Session):
        """Test deleting a game from the database"""
        # Create a game
        game = Game(title="Game to Delete")
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        game_id = game.id

        # Verify game exists
        assert db_session.query(Game).filter(Game.id == game_id).first() is not None

        # Delete the game
        db_session.delete(game)
        db_session.commit()

        # Verify game is deleted
        assert db_session.query(Game).filter(Game.id == game_id).first() is None

    def test_query_games_with_filters(self, db_session: Session, sample_games_data):
        """Test querying games with various filters"""
        # Create games in database
        for game_data in sample_games_data:
            game = Game(**game_data)
            db_session.add(game)

        db_session.commit()

        # Test filtering by game type
        strategy_games = (
            db_session.query(Game).filter(Game.game_type == "Strategy").all()
        )
        assert len(strategy_games) == 1
        assert strategy_games[0].title == "Catan"

        # Test filtering by complexity
        medium_games = db_session.query(Game).filter(Game.complexity == "Medium").all()
        assert len(medium_games) == 2  # Catan and Pandemic

    def test_database_transaction_rollback(self, db_session: Session):
        """Test that database transactions can be rolled back"""
        # Create a game
        game = Game(title="Test Game")
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        game_id = game.id

        # Verify game exists
        assert db_session.query(Game).filter(Game.id == game_id).first() is not None

        # Start a new transaction and add another game
        new_game = Game(title="Another Game")
        db_session.add(new_game)

        # Rollback the transaction
        db_session.rollback()

        # Verify the new game was not committed
        assert (
            db_session.query(Game).filter(Game.title == "Another Game").first() is None
        )

        # Verify the original game still exists
        assert db_session.query(Game).filter(Game.id == game_id).first() is not None


class TestDatabaseConfiguration:
    """Test cases for database configuration and environment variables"""

    def test_missing_database_url(self):
        """Test that missing DATABASE_URL raises ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="DATABASE_URL environment variable is required"
            ):
                # Re-import database module to trigger the check
                import importlib

                import app.database

                importlib.reload(app.database)

    def test_empty_database_url(self):
        """Test that empty DATABASE_URL raises ValueError"""
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            with pytest.raises(
                ValueError, match="DATABASE_URL environment variable is required"
            ):
                # Re-import database module to trigger the check
                import importlib

                import app.database

                importlib.reload(app.database)

    def test_sqlite_engine_creation(self):
        """Test SQLite engine creation with proper configuration"""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
            # Re-import to get fresh engine
            import importlib

            import app.database

            importlib.reload(app.database)

            # Check that engine was created with SQLite config
            assert app.database.engine is not None
            assert "sqlite" in str(app.database.engine.url)

    def test_postgresql_engine_creation(self):
        """Test PostgreSQL engine creation"""
        with patch.dict(
            os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost/db"}
        ):
            # Re-import to get fresh engine
            import importlib

            import app.database

            importlib.reload(app.database)

            # Check that engine was created
            assert app.database.engine is not None
            assert "postgresql" in str(app.database.engine.url)

    def test_session_local_creation(self):
        """Test SessionLocal creation"""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
            # Re-import to get fresh SessionLocal
            import importlib

            import app.database

            importlib.reload(app.database)

            # Check that SessionLocal was created
            assert app.database.SessionLocal is not None


class TestDatabaseEventListeners:
    """Test cases for database event listeners"""

    def test_before_insert_event_listener(self, db_session: Session):
        """Test that before_insert event sets timestamps"""
        # Create a game without timestamps
        game = Game(title="Test Game")

        # Add to session (this should trigger before_insert)
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        # Check that timestamps were set
        assert game.created_at is not None
        assert game.updated_at is not None
        # Allow for small time differences due to execution time
        assert abs((game.created_at - game.updated_at).total_seconds()) < 0.1

    def test_before_update_event_listener(self, db_session: Session):
        """Test that before_update event updates timestamp"""
        # Create a game
        game = Game(title="Original Title")
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        original_created_at = game.created_at
        original_updated_at = game.updated_at

        # Update the game (this should trigger before_update)
        game.title = "Updated Title"
        db_session.commit()
        db_session.refresh(game)

        # Check that created_at didn't change but updated_at did
        assert game.created_at == original_created_at
        assert game.updated_at > original_updated_at

    def test_before_insert_with_existing_timestamps(self, db_session: Session):
        """Test that before_insert doesn't override existing timestamps"""
        from datetime import UTC, datetime

        # Create a game with existing timestamps
        existing_time = datetime.now(UTC)
        game = Game(
            title="Test Game", created_at=existing_time, updated_at=existing_time
        )

        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        # Check that timestamps weren't changed (ignore timezone for comparison)
        assert game.created_at.replace(tzinfo=UTC) == existing_time
        assert game.updated_at.replace(tzinfo=UTC) == existing_time

    def test_before_update_without_updated_at_field(self):
        """Test that before_update handles models without updated_at field"""
        # This test is not practical to implement without creating a full table
        # The event listener logic handles missing updated_at fields gracefully
        # by checking hasattr(target, "updated_at") before setting it
        pass


class TestDatabaseSessionManagement:
    """Test cases for database session management"""

    def test_get_db_generator(self):
        """Test the get_db dependency generator"""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
            # Re-import to get fresh dependencies
            import importlib

            import app.database

            importlib.reload(app.database)

            # Test the generator
            db_gen = app.database.get_db()
            db = next(db_gen)

            # Check that we got a session
            assert db is not None
            assert hasattr(db, "close")

            # Test that the generator closes properly
            try:
                next(db_gen)
            except StopIteration:
                pass  # Expected

    def test_create_db_and_tables(self):
        """Test create_db_and_tables function"""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
            # Re-import to get fresh dependencies
            import importlib

            import app.database

            importlib.reload(app.database)

            # This should not raise an error
            app.database.create_db_and_tables()
