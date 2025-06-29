from datetime import datetime

from app.models import Game


class TestGameModel:
    """Test cases for the Game model"""

    def test_create_game_with_minimal_data(self):
        """Test creating a game with only required fields"""
        game = Game(title="Test Game")

        assert game.title == "Test Game"
        assert game.player_count is None
        assert game.game_type is None
        assert game.playtime is None
        assert game.complexity is None
        assert game.description is None
        # Timestamps are None until saved to database
        assert game.created_at is None
        assert game.updated_at is None

    def test_create_game_with_all_fields(self):
        """Test creating a game with all fields"""
        game = Game(
            title="Catan",
            player_count="3-4 players",
            game_type="Strategy",
            playtime="60-90 minutes",
            complexity="Medium",
            description="A classic strategy game about building settlements",
        )

        assert game.title == "Catan"
        assert game.player_count == "3-4 players"
        assert game.game_type == "Strategy"
        assert game.playtime == "60-90 minutes"
        assert game.complexity == "Medium"
        assert game.description == "A classic strategy game about building settlements"

    def test_game_repr(self):
        """Test the string representation of a game"""
        game = Game(id=1, title="Test Game")
        assert repr(game) == "<Game(id=1, title='Test Game')>"

    def test_game_timestamps_after_save(self, db_session):
        """Test that timestamps are set when saved to database"""
        game = Game(title="Test Game")

        # Before saving, timestamps should be None
        assert game.created_at is None
        assert game.updated_at is None

        # Save to database
        db_session.add(game)
        db_session.commit()
        db_session.refresh(game)

        # After saving, timestamps should be set
        assert game.created_at is not None
        assert game.updated_at is not None

        # Check that they are datetime objects
        assert isinstance(game.created_at, datetime)
        assert isinstance(game.updated_at, datetime)

        # Check that they are close (within 1 second) since they're set at slightly different times
        time_diff = abs((game.updated_at - game.created_at).total_seconds())
        assert time_diff < 1.0

    def test_game_string_fields(self):
        """Test that string fields can be empty or None"""
        game = Game(
            title="Test Game",
            player_count="",
            game_type=None,
            playtime="",
            complexity=None,
        )

        assert game.player_count == ""
        assert game.game_type is None
        assert game.playtime == ""
        assert game.complexity is None
