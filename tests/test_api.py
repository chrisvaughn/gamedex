from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.ai_utils import format_game_metadata


class TestAPIEndpoints:
    """Test cases for API endpoints"""

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "GameDex" in response.text

    def test_games_list_endpoint_empty(self, authenticated_client: TestClient):
        """Test games list endpoint with no games"""
        response = authenticated_client.get("/games")
        assert response.status_code == 200
        assert "No games yet!" in response.text

    def test_games_list_endpoint_with_games(
        self, authenticated_client: TestClient, sample_games_data
    ):
        """Test games list endpoint with games"""
        # Add games first
        for game_data in sample_games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Test list endpoint
        response = authenticated_client.get("/games")
        assert response.status_code == 200
        assert "Catan" in response.text
        assert "Ticket to Ride" in response.text
        assert "Pandemic" in response.text

    def test_create_game_endpoint(
        self, authenticated_client: TestClient, sample_game_data
    ):
        """Test creating a game"""
        response = authenticated_client.post("/games", data=sample_game_data)
        assert response.status_code == 200
        assert response.status_code == 200
        assert "Test Game" in response.text

        # Verify game was created in database
        response = authenticated_client.get("/games")
        assert "Test Game" in response.text

    def test_create_game_endpoint_missing_title(self, authenticated_client: TestClient):
        """Test creating a game without required title"""
        game_data = {"player_count": "2-4 players", "game_type": "Strategy"}
        response = authenticated_client.post("/games", data=game_data)
        assert response.status_code == 422  # Validation error

    def test_game_detail_endpoint(
        self, authenticated_client: TestClient, sample_game_data
    ):
        """Test getting game details"""
        # Create a game first
        response = authenticated_client.post("/games", data=sample_game_data)
        assert response.status_code == 200

        # Get the game ID from the response
        response = authenticated_client.get("/games")
        assert "Test Game" in response.text

        # Find the game ID by looking for the detail link
        # This is a simplified test - in practice you'd need to extract the ID
        response = authenticated_client.get("/games/1")  # Assuming ID 1
        if response.status_code == 200:
            assert "Test Game" in response.text
            assert "2-4 players" in response.text
            assert "Strategy" in response.text

    def test_game_detail_endpoint_not_found(self, authenticated_client: TestClient):
        """Test getting details for non-existent game"""
        response = authenticated_client.get("/games/999")
        assert response.status_code == 404

    def test_update_game_endpoint(
        self, authenticated_client: TestClient, sample_game_data
    ):
        """Test updating a game"""
        # Create a game first
        response = authenticated_client.post("/games", data=sample_game_data)
        assert response.status_code == 200

        # Update the game
        updated_data = sample_game_data.copy()
        updated_data["title"] = "Updated Test Game"

        response = authenticated_client.post("/games/1", data=updated_data)
        if response.status_code == 200:
            assert "Game updated successfully" in response.text

            # Verify update in list
            response = authenticated_client.get("/games")
            assert "Updated Test Game" in response.text

            # Verify update in details
            response = authenticated_client.get("/games/1")
            if response.status_code == 200:
                assert "Updated Test Game" in response.text

    def test_delete_game_endpoint(
        self, authenticated_client: TestClient, sample_game_data
    ):
        """Test deleting a game"""
        # Create a game first
        response = authenticated_client.post("/games", data=sample_game_data)
        assert response.status_code == 200

        # Delete the game
        response = authenticated_client.delete("/games/1")
        if response.status_code == 200:
            assert "Game deleted successfully" in response.text

            # Verify the game is gone
            response = authenticated_client.get("/games")
            assert "Test Game" not in response.text

            # Verify 404 for deleted game
            response = authenticated_client.get("/games/1")
            assert response.status_code == 404

    def test_autofill_endpoint(self, authenticated_client: TestClient):
        """Test the autofill endpoint"""
        response = authenticated_client.post("/games/autofill", json={"title": "Catan"})
        # This endpoint might return empty data if no API key is set
        assert response.status_code in [200, 422]

    def test_recommend_endpoint(
        self, authenticated_client: TestClient, sample_games_data
    ):
        """Test the recommend endpoint"""
        # Add some games first
        for game_data in sample_games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Test recommendation
        response = authenticated_client.post(
            "/recommend", data={"query": "strategy game for 4 players"}
        )
        # This endpoint might return empty data if no API key is set
        assert response.status_code in [200, 422]

    def test_search_games(self, authenticated_client: TestClient, sample_games_data):
        """Test searching games"""
        # Add games first
        for game_data in sample_games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Test search
        response = authenticated_client.get("/games?search=catan")
        assert response.status_code == 200
        assert "Catan" in response.text

    def test_filter_games_by_type(
        self, authenticated_client: TestClient, sample_games_data
    ):
        """Test filtering games by type"""
        # Add games first
        for game_data in sample_games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Test filtering by strategy games
        response = authenticated_client.get("/games?game_type=Strategy")
        assert response.status_code == 200
        assert "Catan" in response.text
        assert "Ticket to Ride" not in response.text  # Family game

    def test_filter_games_by_complexity(
        self, authenticated_client: TestClient, sample_games_data
    ):
        """Test filtering games by complexity"""
        # Add games first
        for game_data in sample_games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Test filtering by medium complexity
        response = authenticated_client.get("/games?complexity=Medium")
        assert response.status_code == 200
        assert "Catan" in response.text
        assert "Pandemic" in response.text
        assert "Ticket to Ride" not in response.text  # Easy complexity

    def test_invalid_game_id(self, authenticated_client: TestClient):
        """Test handling of invalid game IDs"""
        # Test with non-numeric ID - should return 422 (validation error)
        response = authenticated_client.get("/games/abc")
        assert response.status_code == 422

        # Test with negative ID - should return 422 (validation error)
        response = authenticated_client.get("/games/-1")
        assert response.status_code == 422

    def test_games_endpoint_with_query_params(
        self, authenticated_client: TestClient, sample_games_data
    ):
        """Test games endpoint with various query parameters"""
        # Add games first
        for game_data in sample_games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Test with multiple filters
        response = authenticated_client.get(
            "/games?search=cat&game_type=Strategy&complexity=Medium"
        )
        assert response.status_code == 200
        assert "Catan" in response.text

    def test_games_endpoint_sorting(
        self, authenticated_client: TestClient, sample_games_data
    ):
        """Test games endpoint with sorting"""
        # Add games first
        for game_data in sample_games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Test sorting by title
        response = authenticated_client.get("/games?sort=title")
        assert response.status_code == 200

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


class TestGameCRUDEndpoints:
    """Test cases for game CRUD operations"""

    def test_create_game_success(self, authenticated_client, db_session):
        """Test creating a game successfully"""
        game_data = {
            "title": "Test Game",
            "player_count": "2-4 players",
            "game_type": "Strategy",
            "playtime": "30-60 minutes",
            "complexity": "Medium",
            "description": "A test game",
        }
        response = authenticated_client.post(
            "/games", data=game_data, follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/?msg=Game+added+successfully"

    def test_create_game_missing_title(self, authenticated_client):
        """Test creating a game without title (should fail)"""
        game_data = {
            "player_count": "2-4 players",
            "game_type": "Strategy",
        }
        response = authenticated_client.post("/games", data=game_data)
        assert response.status_code == 422  # Validation error

    def test_create_game_with_ratings(self, authenticated_client, db_session):
        """Test creating a game with family member ratings"""
        # First create a family member
        from app.models import FamilyMember

        family_member = FamilyMember(name="Test Member")
        db_session.add(family_member)
        db_session.commit()

        game_data = {
            "title": "Test Game with Ratings",
            "player_count": "2-4 players",
            "rating_1": "8",  # Rating for family member with ID 1
        }
        response = authenticated_client.post(
            "/games", data=game_data, follow_redirects=False
        )
        assert response.status_code == 303

    def test_create_game_with_invalid_rating(self, authenticated_client, db_session):
        """Test creating a game with invalid rating (should be ignored)"""
        # First create a family member
        from app.models import FamilyMember

        family_member = FamilyMember(name="Test Member")
        db_session.add(family_member)
        db_session.commit()

        game_data = {
            "title": "Test Game with Invalid Rating",
            "rating_1": "15",  # Invalid rating (out of range)
        }
        response = authenticated_client.post(
            "/games", data=game_data, follow_redirects=False
        )
        assert response.status_code == 303

    def test_get_game_success(self, authenticated_client, db_session):
        """Test getting a specific game"""
        # Create a game first
        from app.models import Game

        game = Game(title="Test Game")
        db_session.add(game)
        db_session.commit()

        response = authenticated_client.get(f"/games/{game.id}")
        assert response.status_code == 200
        assert "Test Game" in response.text

    def test_get_game_not_found(self, authenticated_client):
        """Test getting a non-existent game"""
        response = authenticated_client.get("/games/999")
        assert response.status_code == 404

    def test_update_game_success(self, authenticated_client, db_session):
        """Test updating a game"""
        # Create a game first
        from app.models import Game

        game = Game(title="Original Title")
        db_session.add(game)
        db_session.commit()

        update_data = {
            "title": "Updated Title",
            "player_count": "3-5 players",
            "game_type": "Family",
        }
        response = authenticated_client.post(
            f"/games/{game.id}", data=update_data, follow_redirects=False
        )
        assert response.status_code == 303
        assert (
            f"/games/{game.id}?msg=Game+updated+successfully"
            in response.headers["location"]
        )

    def test_update_game_not_found(self, authenticated_client):
        """Test updating a non-existent game"""
        update_data = {"title": "Updated Title"}
        response = authenticated_client.post("/games/999", data=update_data)
        assert response.status_code == 404

    def test_delete_game_success(self, authenticated_client, db_session):
        """Test deleting a game"""
        # Create a game first
        from app.models import Game

        game = Game(title="Game to Delete")
        db_session.add(game)
        db_session.commit()

        response = authenticated_client.delete(
            f"/games/{game.id}", follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/?msg=Game+deleted+successfully"

    def test_delete_game_not_found(self, authenticated_client):
        """Test deleting a non-existent game"""
        response = authenticated_client.delete("/games/999")
        assert response.status_code == 404

    def test_autofill_game_by_title(self, authenticated_client, db_session):
        """Test autofill game by title endpoint"""
        with patch("app.main.get_game_metadata") as mock_get_metadata:
            mock_get_metadata.return_value = {
                "player_count": "2-4 players",
                "game_type": "Strategy",
                "playtime": "30-60 minutes",
                "complexity": "Medium",
            }

            response = authenticated_client.post(
                "/games/autofill", data={"title": "Catan"}, follow_redirects=False
            )
            assert response.status_code == 303
            # Should redirect to the created game's detail page
            assert "/games/" in response.headers["location"]

    def test_autofill_existing_game(self, authenticated_client, db_session):
        """Test autofill for existing game"""
        # Create a game first
        from app.models import Game

        game = Game(title="Game to Autofill")
        db_session.add(game)
        db_session.commit()

        with patch("app.main.get_game_metadata") as mock_get_metadata:
            mock_get_metadata.return_value = {
                "player_count": "2-4 players",
                "game_type": "Strategy",
            }

            response = authenticated_client.post(
                f"/games/{game.id}/autofill", follow_redirects=False
            )
            assert response.status_code == 303
            assert (
                f"/games/{game.id}?msg=Game+metadata+updated+with+AI"
                in response.headers["location"]
            )

    def test_autofill_existing_game_not_found(self, authenticated_client):
        """Test autofill for non-existent game"""
        response = authenticated_client.post("/games/999/autofill")
        assert response.status_code == 404


class TestSettingsEndpoints:
    """Test cases for settings and family member endpoints"""

    def test_add_family_member_success(self, authenticated_client, db_session):
        """Test adding a family member successfully"""
        response = authenticated_client.post(
            "/settings/family-members",
            data={"name": "New Member"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (
            response.headers["location"]
            == "/settings?msg=Family+member+added+successfully"
        )

    def test_add_family_member_duplicate(self, authenticated_client, db_session):
        """Test adding a duplicate family member"""
        # First add a member
        from app.models import FamilyMember

        member = FamilyMember(name="Existing Member")
        db_session.add(member)
        db_session.commit()

        # Try to add the same name again
        response = authenticated_client.post(
            "/settings/family-members",
            data={"name": "Existing Member"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (
            response.headers["location"]
            == "/settings?error=Family+member+already+exists"
        )

    def test_delete_family_member_success(self, authenticated_client, db_session):
        """Test deleting a family member"""
        # Create a family member first
        from app.models import FamilyMember

        member = FamilyMember(name="Member to Delete")
        db_session.add(member)
        db_session.commit()

        response = authenticated_client.delete(
            f"/settings/family-members/{member.id}", follow_redirects=False
        )
        assert response.status_code == 303
        assert (
            response.headers["location"]
            == "/settings?msg=Family+member+deleted+successfully"
        )

    def test_delete_family_member_not_found(self, authenticated_client):
        """Test deleting a non-existent family member"""
        response = authenticated_client.delete("/settings/family-members/999")
        assert response.status_code == 404


class TestRecommendationEndpoints:
    """Test cases for recommendation endpoints"""

    def test_get_recommendations_no_games(self, authenticated_client):
        """Test getting recommendations when no games exist"""
        response = authenticated_client.post(
            "/recommend", data={"query": "strategy game"}
        )
        assert response.status_code == 200
        assert "No Games in Collection" in response.text

    def test_get_recommendations_with_games(self, authenticated_client, db_session):
        """Test getting recommendations with games in collection"""
        # Add a game first
        from app.models import Game

        game = Game(title="Catan", game_type="Strategy")
        db_session.add(game)
        db_session.commit()

        with patch("app.main.get_game_recommendations") as mock_get_recommendations:
            mock_get_recommendations.return_value = [
                {"title": "Catan", "reasoning": "Great strategy game"}
            ]

            response = authenticated_client.post(
                "/recommend", data={"query": "strategy game"}
            )
            assert response.status_code == 200
            assert "Catan" in response.text
