from unittest.mock import MagicMock, patch

import pytest

from app.ai_utils import (
    format_game_metadata,
    get_game_metadata,
    get_game_recommendations,
)


class TestAIFunctions:
    """Test cases for AI utility functions"""

    @patch("app.ai_utils.os.getenv")
    @patch("app.ai_utils.client")
    async def test_get_game_metadata_success(self, mock_client, mock_getenv):
        """Test successful game metadata retrieval"""
        # Mock environment variable
        mock_getenv.return_value = "test-api-key"

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
        {
            "title": "Catan",
            "player_count": "2-4 players",
            "game_type": "Strategy",
            "playtime": "30-60 minutes",
            "complexity": "Medium",
            "description": "A classic strategy game"
        }
        """
        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = await get_game_metadata("Catan")

        # Verify the result
        assert result["title"] == "Catan"
        assert result["player_count"] == "2-4 players"
        assert result["game_type"] == "Strategy"
        assert result["playtime"] == "30-60 minutes"
        assert result["complexity"] == "Medium"
        assert result["description"] == "A classic strategy game"

        # Verify OpenAI was called correctly
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.ai_utils.os.getenv")
    async def test_get_game_metadata_no_api_key(self, mock_getenv):
        """Test game metadata retrieval without API key"""
        # Mock no API key
        mock_getenv.return_value = None

        # Test the function
        result = await get_game_metadata("Catan")

        # Should return empty dict
        assert result == {}

    @patch("app.ai_utils.os.getenv")
    @patch("app.ai_utils.client")
    async def test_get_game_metadata_invalid_json(self, mock_client, mock_getenv):
        """Test game metadata retrieval with invalid JSON response"""
        # Mock environment variable
        mock_getenv.return_value = "test-api-key"

        # Mock OpenAI response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not valid JSON"
        mock_client.chat.completions.create.return_value = mock_response

        # Test the function
        result = await get_game_metadata("Catan")

        # Should return fallback structure
        assert "title" in result
        assert "player_count" in result
        assert "game_type" in result
        assert "playtime" in result
        assert "complexity" in result
        assert result["description"] == "This is not valid JSON"

    @patch("app.ai_utils.os.getenv")
    @patch("app.ai_utils.client")
    async def test_get_game_metadata_exception(self, mock_client, mock_getenv):
        """Test game metadata retrieval with exception"""
        # Mock environment variable
        mock_getenv.return_value = "test-api-key"

        # Mock OpenAI to raise exception
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        # Test the function
        result = await get_game_metadata("Catan")

        # Should return empty dict on error
        assert result == {}

    @patch("app.ai_utils.os.getenv")
    @patch("app.ai_utils.client")
    async def test_get_game_recommendations_success(self, mock_client, mock_getenv):
        """Test successful game recommendations"""
        # Mock environment variable
        mock_getenv.return_value = "test-api-key"

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
        [
            {
                "title": "Catan",
                "reasoning": "Great for 4 players and strategic gameplay"
            },
            {
                "title": "Ticket to Ride",
                "reasoning": "Easy to learn and fun for groups"
            }
        ]
        """
        mock_client.chat.completions.create.return_value = mock_response

        # Sample games data
        available_games = [
            {"title": "Catan", "player_count": "3-4", "game_type": "Strategy"},
            {"title": "Ticket to Ride", "player_count": "2-5", "game_type": "Family"},
        ]

        # Test the function
        result = await get_game_recommendations(
            "We want a strategy game for 4 players", available_games
        )

        # Verify the result
        assert len(result) == 2
        assert result[0]["title"] == "Catan"
        assert result[0]["reasoning"] == "Great for 4 players and strategic gameplay"
        assert result[1]["title"] == "Ticket to Ride"
        assert result[1]["reasoning"] == "Easy to learn and fun for groups"

    @patch("app.ai_utils.os.getenv")
    async def test_get_game_recommendations_no_api_key(self, mock_getenv):
        """Test game recommendations without API key"""
        # Mock no API key
        mock_getenv.return_value = None

        # Test the function
        result = await get_game_recommendations("test query", [])

        # Should return empty list
        assert result == []

    @patch("app.ai_utils.os.getenv")
    async def test_get_game_recommendations_no_games(self, mock_getenv):
        """Test game recommendations with no available games"""
        # Mock environment variable
        mock_getenv.return_value = "test-api-key"

        # Test the function
        result = await get_game_recommendations("test query", [])

        # Should return empty list
        assert result == []

    def test_format_game_metadata(self):
        """Test formatting game metadata"""
        # Test with normal metadata
        metadata = {
            "player_count": "2-4 players",
            "game_type": "Strategy",
            "playtime": "30-60 minutes",
            "complexity": "Medium",
            "description": "A classic strategy game",
        }

        result = format_game_metadata(metadata)

        assert result["player_count"] == "2-4 players"
        assert result["game_type"] == "Strategy"
        assert result["playtime"] == "30-60 minutes"
        assert result["complexity"] == "Medium"
        assert result["description"] == "A classic strategy game"

    def test_format_game_metadata_with_whitespace(self):
        """Test formatting metadata with extra whitespace"""
        metadata = {
            "player_count": "  2-4 players  ",
            "game_type": "Strategy\n",
            "playtime": "30-60\nminutes",
            "complexity": "Medium\t",
            "description": "A classic\n\tstrategy game",
        }

        result = format_game_metadata(metadata)

        assert result["player_count"] == "2-4 players"
        assert result["game_type"] == "Strategy"
        assert result["playtime"] == "30-60 minutes"
        assert result["complexity"] == "Medium"
        assert result["description"] == "A classic strategy game"

    def test_format_game_metadata_with_empty_values(self):
        """Test formatting metadata with empty values"""
        metadata = {
            "player_count": "",
            "game_type": None,
            "playtime": "   ",
            "complexity": "",
            "description": "Valid description",
        }

        result = format_game_metadata(metadata)

        # Only non-empty, non-None, non-whitespace fields should be included, but empty strings from whitespace are included
        assert "player_count" not in result
        assert "game_type" not in result
        assert "complexity" not in result
        # 'playtime' is included as an empty string
        assert "playtime" in result and result["playtime"] == ""
        # Valid description should be cleaned and included
        assert result["description"] == "Valid description"
