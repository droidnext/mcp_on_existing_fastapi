#!/usr/bin/env python3
"""
Test script to demonstrate FastMCP elicitation functionality.
This script shows how to use the enhanced suggest_movie tool with and without elicitation.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from app.models.elicitation import UserPreferences, RecommendationFeedback

async def elicitation_handler(message: str, response_type: type, params, context):
    """
    Simple elicitation handler for testing.
    This simulates user input during the elicitation process.
    """
    print(f"\n🤖 Server asks: {message}")
    
    if response_type == UserPreferences:
        print("📝 Please provide your movie preferences:")
        
        # Simulate user input for preferences
        preferred_genres = ["Action", "Comedy", "Drama"]
        max_duration = 150
        min_rating = "PG-13"
        include_foreign = True
        preferred_decade = "2010s"
        mood = "exciting"
        
        print(f"   Using preferences: {preferred_genres}, max duration: {max_duration}min, rating: {min_rating}+")
        
        return UserPreferences(
            preferred_genres=preferred_genres,
            max_duration_minutes=max_duration,
            min_rating=min_rating,
            include_foreign_films=include_foreign,
            preferred_decade=preferred_decade,
            mood=mood
        )
    
    elif response_type == RecommendationFeedback:
        print("💬 Please provide feedback on the recommendations:")
        
        # Simulate user feedback
        liked_movies = ["The Dark Knight", "Inception", "The Matrix"]
        disliked_movies = []
        additional_preferences = "I really enjoyed the action sequences and complex plots"
        rating_accuracy = 5
        
        print(f"   Feedback: Liked {liked_movies}, accuracy rating: {rating_accuracy}/5")
        
        return RecommendationFeedback(
            liked_movies=liked_movies,
            disliked_movies=disliked_movies,
            additional_preferences=additional_preferences,
            rating_accuracy=rating_accuracy
        )
    
    else:
        print(f"❓ Unknown response type: {response_type}")
        return ElicitResult(action="decline")

async def test_traditional_mode():
    """Test the traditional mode without elicitation"""
    print("\n" + "="*60)
    print("🎬 TESTING TRADITIONAL MODE (No Elicitation)")
    print("="*60)
    
    client = Client(
        "app/mcp/mcp_routes.py",
        elicitation_handler=elicitation_handler
    )
    
    try:
        # Test traditional mode - immediate results
        print("\n📋 Testing suggest_movie with genre='Action' (traditional mode):")
        result = await client.suggest_movie(genre="Action", use_elicitation=False)
        print(f"\n✅ Result:\n{result}")
        
    except Exception as e:
        print(f"❌ Error in traditional mode: {e}")
    
    finally:
        await client.close()

async def test_elicitation_mode():
    """Test the elicitation mode"""
    print("\n" + "="*60)
    print("🎯 TESTING ELICITATION MODE")
    print("="*60)
    
    client = Client(
        "app/mcp/mcp_routes.py",
        elicitation_handler=elicitation_handler
    )
    
    try:
        # Test elicitation mode - interactive preference gathering
        print("\n📋 Testing suggest_movie with use_elicitation=True:")
        result = await client.suggest_movie(use_elicitation=True)
        print(f"\n✅ Result:\n{result}")
        
    except Exception as e:
        print(f"❌ Error in elicitation mode: {e}")
    
    finally:
        await client.close()

async def main():
    """Main test function"""
    print("🚀 FastMCP Elicitation Test")
    print("This script demonstrates the difference between traditional and elicitation modes")
    
    # Test traditional mode first
    await test_traditional_mode()
    
    # Test elicitation mode
    await test_elicitation_mode()
    
    print("\n" + "="*60)
    print("🎉 Testing complete!")
    print("="*60)
    print("\nKey differences observed:")
    print("1. Traditional mode: Immediate results based on genre")
    print("2. Elicitation mode: Interactive preference gathering for personalized results")
    print("3. Elicitation provides more tailored recommendations based on user input")

if __name__ == "__main__":
    asyncio.run(main())
