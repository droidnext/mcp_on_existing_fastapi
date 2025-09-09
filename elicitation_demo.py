#!/usr/bin/env python3
"""
Simplified Elicitation Demonstration
This script demonstrates the elicitation concept without requiring the full MCP infrastructure.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional, List
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.elicitation import UserPreferences, RecommendationFeedback
from app.models.movie import Genre, Rating

@dataclass
class MockMovie:
    """Mock movie object for demonstration"""
    title: str
    description: str
    duration: int
    genres: List[str]
    rating: str
    imdb_rating: Optional[float] = None
    average_rating: float = 4.0

class MockMovieService:
    """Mock movie service for demonstration"""
    
    def __init__(self):
        # Create some sample movies
        self.movies = [
            MockMovie(
                title="The Dark Knight",
                description="When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                duration=152,
                genres=["Action", "Crime", "Drama"],
                rating="PG-13",
                imdb_rating=9.0,
                average_rating=4.7
            ),
            MockMovie(
                title="Inception",
                description="A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
                duration=148,
                genres=["Action", "Science Fiction", "Thriller"],
                rating="PG-13",
                imdb_rating=8.8,
                average_rating=4.6
            ),
            MockMovie(
                title="The Matrix",
                description="A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
                duration=136,
                genres=["Action", "Science Fiction"],
                rating="R",
                imdb_rating=8.7,
                average_rating=4.5
            ),
            MockMovie(
                title="Pulp Fiction",
                description="The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
                duration=154,
                genres=["Crime", "Drama"],
                rating="R",
                imdb_rating=8.9,
                average_rating=4.3
            ),
            MockMovie(
                title="Forrest Gump",
                description="The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75.",
                duration=142,
                genres=["Drama", "Romance"],
                rating="PG-13",
                imdb_rating=8.8,
                average_rating=4.4
            )
        ]
    
    async def get_by_genre(self, genre: str) -> List[MockMovie]:
        """Get movies by genre"""
        return [movie for movie in self.movies if genre.lower() in [g.lower() for g in movie.genres]]
    
    async def get_all_movies(self) -> List[MockMovie]:
        """Get all movies"""
        return self.movies

class MockElicitationContext:
    """Mock elicitation context for demonstration"""
    
    async def elicit(self, message: str, response_type: type, description: str = None):
        """Mock elicitation that simulates user input"""
        print(f"\n🤖 Server asks: {message}")
        if description:
            print(f"📝 Description: {description}")
        
        # Simulate user input based on response type
        if response_type == UserPreferences:
            return await self._mock_user_preferences()
        elif response_type == RecommendationFeedback:
            return await self._mock_feedback()
        else:
            return None
    
    async def _mock_user_preferences(self) -> UserPreferences:
        """Mock user preferences input"""
        print("📝 Simulating user input for preferences...")
        
        # Simulate user providing preferences
        preferences = UserPreferences(
            preferred_genres=["Action", "Science Fiction"],
            max_duration_minutes=150,
            min_rating="PG-13",
            include_foreign_films=True,
            preferred_decade="2000s",
            mood="exciting"
        )
        
        print(f"   User provided: {preferences.preferred_genres} genres, max {preferences.max_duration_minutes}min, {preferences.min_rating}+ rating")
        return preferences
    
    async def _mock_feedback(self) -> RecommendationFeedback:
        """Mock user feedback input"""
        print("💬 Simulating user feedback...")
        
        feedback = RecommendationFeedback(
            liked_movies=["The Dark Knight", "Inception"],
            disliked_movies=[],
            additional_preferences="I really enjoyed the complex plots and action sequences",
            rating_accuracy=5
        )
        
        print(f"   User feedback: Liked {feedback.liked_movies}, accuracy rating: {feedback.rating_accuracy}/5")
        return feedback

async def suggest_movie_traditional(genre: str) -> str:
    """Traditional movie suggestion without elicitation"""
    print(f"\n🎬 Traditional Mode: Suggesting movies for genre '{genre}'")
    
    movie_service = MockMovieService()
    movies = await movie_service.get_by_genre(genre)
    
    if not movies:
        return f"No movies found in the {genre} genre."
    
    response = f"Here are the {genre} movies:\n\n"
    for movie in movies:
        response += f"🎬 {movie.title}\n"
        response += f"📝 {movie.description}\n"
        response += f"⭐ Rating: {movie.rating}\n"
        response += f"🎭 Genres: {', '.join(movie.genres)}\n"
        if movie.imdb_rating:
            response += f"📊 IMDB Rating: {movie.imdb_rating}/10\n"
        response += "\n"
    
    return response

async def suggest_movie_with_elicitation() -> str:
    """Movie suggestion with elicitation for personalized recommendations"""
    print(f"\n🎯 Elicitation Mode: Gathering user preferences for personalized recommendations")
    
    context = MockElicitationContext()
    movie_service = MockMovieService()
    
    # First elicitation: Get user preferences
    preferences = await context.elicit(
        "What are your movie preferences?",
        UserPreferences,
        description="Please tell us about your movie preferences so we can provide better recommendations."
    )
    
    if not preferences:
        return "No preferences provided. Here are some general recommendations..."
    
    # Use preferences to get recommendations
    all_movies = await movie_service.get_all_movies()
    filtered_movies = []
    
    for movie in all_movies:
        # Filter by genres
        if preferences.preferred_genres:
            if not any(genre.lower() in [g.lower() for g in movie.genres] for genre in preferences.preferred_genres):
                continue
        
        # Filter by duration
        if preferences.max_duration_minutes and movie.duration > preferences.max_duration_minutes:
            continue
        
        # Filter by rating
        if preferences.min_rating:
            try:
                if movie.rating < preferences.min_rating:
                    continue
            except:
                pass
        
        filtered_movies.append(movie)
    
    # Sort by rating and return top results
    filtered_movies.sort(key=lambda x: x.average_rating, reverse=True)
    top_movies = filtered_movies[:3]
    
    response = "Here are your personalized recommendations:\n\n"
    for movie in top_movies:
        response += f"🎬 {movie.title}\n"
        response += f"📝 {movie.description}\n"
        response += f"⭐ Rating: {movie.rating}\n"
        response += f"🎭 Genres: {', '.join(movie.genres)}\n"
        if movie.imdb_rating:
            response += f"📊 IMDB Rating: {movie.imdb_rating}/10\n"
        response += "\n"
    
    # Second elicitation: Get feedback for future improvements
    feedback = await context.elicit(
        "How did you like these recommendations?",
        RecommendationFeedback,
        description="Your feedback helps us improve future recommendations."
    )
    
    if feedback and feedback.liked_movies:
        response += f"\n💡 Based on your feedback, we'll remember you liked: {', '.join(feedback.liked_movies[:3])}"
    
    return response

async def main():
    """Main demonstration function"""
    print("🚀 FastMCP Elicitation Demonstration")
    print("This script demonstrates the elicitation concept without requiring the full MCP infrastructure")
    print("=" * 80)
    
    # Test traditional mode
    print("\n" + "="*60)
    print("🎬 TESTING TRADITIONAL MODE (No Elicitation)")
    print("="*60)
    
    try:
        result = await suggest_movie_traditional("Action")
        print(f"\n✅ Result:\n{result}")
    except Exception as e:
        print(f"❌ Error in traditional mode: {e}")
    
    # Test elicitation mode
    print("\n" + "="*60)
    print("🎯 TESTING ELICITATION MODE")
    print("="*60)
    
    try:
        result = await suggest_movie_with_elicitation()
        print(f"\n✅ Result:\n{result}")
    except Exception as e:
        print(f"❌ Error in elicitation mode: {e}")
    
    print("\n" + "="*80)
    print("🎉 Demonstration complete!")
    print("="*80)
    print("\nKey differences observed:")
    print("1. Traditional mode: Immediate results based on genre")
    print("2. Elicitation mode: Interactive preference gathering for personalized results")
    print("3. Elicitation provides more tailored recommendations based on user input")
    print("\nNote: This is a simplified demonstration. In a real MCP implementation:")
    print("- The elicitation would happen through the MCP protocol")
    print("- User input would be collected through the client interface")
    print("- The server would handle multiple concurrent elicitation requests")

if __name__ == "__main__":
    asyncio.run(main())
