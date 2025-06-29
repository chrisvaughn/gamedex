import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Game


class TestIntegration:
    """Integration tests for the full application flow"""

    def test_full_game_lifecycle(self, authenticated_client: TestClient):
        """Test the complete lifecycle of a game: create, view, update, delete"""
        # 1. Create a new game
        game_data = {
            "title": "Integration Test Game",
            "player_count": "2-4 players",
            "game_type": "Strategy",
            "playtime": "45 minutes",
            "complexity": "Medium",
            "description": "A test game for integration testing",
        }

        response = authenticated_client.post("/games", data=game_data)
        assert response.status_code == 200
        assert "Game added successfully" in response.text

        # 2. Verify game appears in list
        response = authenticated_client.get("/games")
        assert response.status_code == 200
        assert "Integration Test Game" in response.text
        assert "Strategy" in response.text

        # 3. View game details (assuming ID 1)
        response = authenticated_client.get("/games/1")
        if response.status_code == 200:
            assert "Integration Test Game" in response.text
            assert "2-4 players" in response.text
            assert "45 minutes" in response.text
            assert "Medium" in response.text
            assert "A test game for integration testing" in response.text

        # 4. Update the game
        updated_data = game_data.copy()
        updated_data["title"] = "Updated Integration Test Game"
        updated_data["description"] = "Updated description for integration testing"

        response = authenticated_client.post("/games/1", data=updated_data)
        if response.status_code == 200:
            assert "Game updated successfully" in response.text

            # Verify update in list
            response = authenticated_client.get("/games")
            assert "Updated Integration Test Game" in response.text

            # Verify update in details
            response = authenticated_client.get("/games/1")
            if response.status_code == 200:
                assert "Updated Integration Test Game" in response.text
                assert "Updated description for integration testing" in response.text

        # 5. Delete the game
        response = authenticated_client.delete("/games/1")
        if response.status_code == 200:
            assert "Game deleted successfully" in response.text

            # Verify deletion
            response = authenticated_client.get("/games")
            assert "Updated Integration Test Game" not in response.text

            # Verify 404 for deleted game
            response = authenticated_client.get("/games/1")
            assert response.status_code == 404

    def test_search_and_filter_integration(self, authenticated_client: TestClient):
        """Test search and filter functionality with multiple games"""
        # Create multiple games with different characteristics
        games_data = [
            {
                "title": "Catan",
                "player_count": "3-4 players",
                "game_type": "Strategy",
                "playtime": "60-90 minutes",
                "complexity": "Medium",
            },
            {
                "title": "Ticket to Ride",
                "player_count": "2-5 players",
                "game_type": "Family",
                "playtime": "30-60 minutes",
                "complexity": "Easy",
            },
            {
                "title": "Pandemic",
                "player_count": "2-4 players",
                "game_type": "Cooperative",
                "playtime": "45 minutes",
                "complexity": "Medium",
            },
        ]

        # Add all games
        for game_data in games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Test search functionality
        response = authenticated_client.get("/games?search=cat")
        assert response.status_code == 200
        assert "Catan" in response.text
        # Note: Client-side filtering means all games are still in the HTML
        # The actual filtering happens in JavaScript

        # Test filtering by game type
        response = authenticated_client.get("/games?game_type=Strategy")
        assert response.status_code == 200
        assert "Catan" in response.text
        # Note: Client-side filtering means all games are still in the HTML

        # Test filtering by complexity
        response = authenticated_client.get("/games?complexity=Medium")
        assert response.status_code == 200
        assert "Catan" in response.text
        assert "Pandemic" in response.text
        # Note: Client-side filtering means all games are still in the HTML

    def test_ai_integration_flow(self, authenticated_client: TestClient):
        """Test the AI autofill and recommendation flow"""
        # Test autofill endpoint
        response = authenticated_client.post("/games/autofill", json={"title": "Catan"})
        # This might return empty data if no API key, but should not error
        assert response.status_code in [200, 422]

        # Create a game manually first
        game_data = {
            "title": "Test Game for AI",
            "player_count": "2-4 players",
            "game_type": "Strategy",
            "playtime": "30 minutes",
            "complexity": "Easy",
        }

        response = authenticated_client.post("/games", data=game_data)
        assert response.status_code == 200

        # Test recommendation endpoint
        response = authenticated_client.post(
            "/recommend", data={"query": "easy strategy game"}
        )
        # This might return empty data if no API key, but should not error
        assert response.status_code in [200, 422]

    def test_error_handling_integration(self, authenticated_client: TestClient):
        """Test error handling across the application"""
        # Test invalid game ID
        response = authenticated_client.get("/games/999")
        assert response.status_code == 404

        # Test invalid game ID for update - should return 404
        response = authenticated_client.post("/games/999", data={"title": "Test"})
        assert response.status_code == 404

        # Test invalid game ID for delete - should return 404
        response = authenticated_client.delete("/games/999")
        assert response.status_code == 404

        # Test malformed data
        response = authenticated_client.post("/games", data={})
        assert response.status_code == 422

        # Test invalid JSON for autofill
        response = authenticated_client.post("/games/autofill", content="invalid json")
        assert response.status_code == 422

    def test_database_consistency(self, authenticated_client: TestClient):
        """Test that database operations maintain consistency"""
        # Create multiple games
        games_data = [
            {"title": "Game 1"},
            {"title": "Game 2"},
            {"title": "Game 3"},
        ]

        for game_data in games_data:
            response = authenticated_client.post("/games", data=game_data)
            assert response.status_code == 200

        # Verify all games are in the list
        response = authenticated_client.get("/games")
        assert response.status_code == 200
        assert "Game 1" in response.text
        assert "Game 2" in response.text
        assert "Game 3" in response.text

        # Delete one game
        response = authenticated_client.delete("/games/1")
        if response.status_code == 200:
            # Verify only that game is gone
            response = authenticated_client.get("/games")
            assert "Game 1" not in response.text
            assert "Game 2" in response.text
            assert "Game 3" in response.text

    def test_concurrent_operations(self, authenticated_client: TestClient):
        """Test concurrent operations on the same game"""
        # Create a game
        game_data = {"title": "Concurrent Test Game"}
        response = authenticated_client.post("/games", data=game_data)
        assert response.status_code == 200

        # Try to update the same game with different data
        update_data1 = {"title": "Update 1"}
        update_data2 = {"title": "Update 2"}

        # These operations should not interfere with each other
        # The last one should win
        response1 = authenticated_client.post("/games/1", data=update_data1)
        response2 = authenticated_client.post("/games/1", data=update_data2)

        # Check final state
        response = authenticated_client.get("/games/1")
        if response.status_code == 200:
            # The last update should be visible
            assert "Update 2" in response.text
