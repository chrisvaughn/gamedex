import json
import os
from typing import Dict, List

from openai import OpenAI

# Configure OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def get_game_metadata(game_title: str) -> Dict[str, str]:
    """
    Use OpenAI GPT to fetch metadata for a board game based on its title.

    Args:
        game_title: The title of the board game

    Returns:
        Dictionary containing game metadata including corrected title
    """
    if not os.getenv("OPENAI_API_KEY"):
        return {}

    try:
        prompt = f"""
        Provide metadata for the board game "{game_title}". Return the information in JSON format with these fields:
        - title: the correct, official title of the game (correct any typos, capitalization, or formatting issues)
        - player_count: typical player count (e.g., "2-4 players")
        - game_type: category/genre (e.g., "Strategy", "Party", "Cooperative")
        - playtime: typical play time (e.g., "30-60 minutes")
        - complexity: complexity level (e.g., "Easy", "Medium", "Hard")
        - description: brief description of the game
        
        If you don't know the game, return an empty JSON object {{}}.
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a board game expert. Provide accurate metadata in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()

        # Try to parse JSON response
        try:
            metadata = json.loads(content)
            return metadata
        except json.JSONDecodeError:
            # Fallback: return basic structure
            return {
                "title": "",
                "player_count": "",
                "game_type": "",
                "playtime": "",
                "complexity": "",
                "description": content,
            }

    except Exception as e:
        print(f"Error fetching game metadata: {e}")
        return {}


async def get_game_recommendations(
    query: str, available_games: List[Dict], max_recommendations: int = 5
) -> List[Dict]:
    """
    Use AI to recommend games based on natural language query.

    Args:
        query: Natural language query (e.g., "We have 4 players and want something quick and funny")
        available_games: List of available games in the collection
        max_recommendations: Maximum number of recommendations to return

    Returns:
        List of recommended games with reasoning
    """
    if not client or not available_games:
        return []

    try:
        games_info = "\n".join(
            [
                f"- {game.get('title', 'Unknown')}: {game.get('player_count', 'N/A')} players, "
                f"{game.get('game_type', 'N/A')}, {game.get('playtime', 'N/A')}, "
                f"Complexity: {game.get('complexity', 'N/A')}"
                for game in available_games
            ]
        )

        prompt = f"""
        Based on this query: "{query}"
        
        And these available games:
        {games_info}
        
        Recommend up to {max_recommendations} games that best match the query. 
        For each recommendation, provide:
        1. Game title
        2. Brief reasoning why it matches the query
        
        Return as JSON array with objects containing "title" and "reasoning" fields.
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a board game recommendation expert. Provide helpful, accurate recommendations.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()

        try:
            recommendations = json.loads(content)
            return recommendations if isinstance(recommendations, list) else []
        except json.JSONDecodeError:
            return []

    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []


def format_game_metadata(metadata: Dict[str, str]) -> Dict[str, str]:
    """
    Format and clean game metadata for display.

    Args:
        metadata: Raw metadata dictionary

    Returns:
        Formatted metadata dictionary
    """
    formatted = {}

    # Clean and format each field
    for key, value in metadata.items():
        if value and isinstance(value, str):
            # Remove extra whitespace and newlines
            cleaned = " ".join(value.split())
            formatted[key] = cleaned

    return formatted
