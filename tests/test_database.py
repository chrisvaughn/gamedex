import pytest
from sqlalchemy.orm import Session

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
