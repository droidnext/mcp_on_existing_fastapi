"""
MCP Elicitation Routes for Movie Recommendation System

This module contains tools that use FastMCP elicitation for interactive
user input gathering. These tools provide personalized recommendations
by asking users about their preferences through structured forms.
"""

import asyncio
import logging
from typing import List

from fastmcp import FastMCP
from fastmcp.server import Context

from app.services.movie_service import MovieService
from app.repositories.movie_repository import FileMovieRepository
from app.models.movie import Genre, Rating, Movie
from app.models.elicitation import (
    UserPreferences, MovieSearchCriteria, RecommendationFeedback
)
from app.core.config import settings
# Import utility functions from main routes
from app.mcp.mcp_routes import trace_tool, with_timeout
import os

# Initialize logger
logger = logging.getLogger("MCP Movie App")

# Initialize FastMCP app for elicitation tools
mcp_elicitation = FastMCP("Movie Elicitation Tools")

# Initialize movie service
movie_repository = FileMovieRepository(os.path.join(os.path.dirname(__file__), "..", "..", "data", "movies.json"))
movie_service = MovieService(movie_repository)

@mcp_elicitation.tool()
@trace_tool("MCP.suggest_movie_elicitation")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def suggest_movie_elicitation(context: Context) -> str:
    """
    Suggest movies using interactive elicitation for personalized recommendations.

    This tool demonstrates elicitation-based movie recommendations by:
    1. Asking users about their movie preferences through structured forms
    2. Providing personalized recommendations based on their responses
    3. Gathering feedback to improve future recommendations

    Args:
        context (Context): The user or session context for personalization.

    Returns:
        str: A formatted string containing personalized movie suggestions.
    """
    logger.info("Starting elicitation-based movie suggestion")
    
    try:
        # First elicitation: Get user preferences
        preferences = await context.elicit(
            "What are your movie preferences?",
            UserPreferences
        )
        
        if not preferences:
            return "No preferences provided. Here are some general recommendations..."
        
        # Use preferences to get recommendations
        movies = await _get_movies_by_preferences(preferences)
        response = _format_movie_list(movies, "personalized recommendations")
        
        # Second elicitation: Get feedback for future improvements
        feedback = await context.elicit(
            "How did you like these recommendations?",
            RecommendationFeedback
        )
        
        if feedback and feedback.liked_movies:
            # Split comma-separated string and take first 3
            liked_list = [movie.strip() for movie in feedback.liked_movies.split(',') if movie.strip()]
            if liked_list:
                response += f"\n\n💡 Based on your feedback, we'll remember you liked: {', '.join(liked_list[:3])}"
            elif feedback.rating_accuracy > 3:
                response += f"\n\n💡 Thank you for the positive feedback (rating: {feedback.rating_accuracy}/5)!"
        
        return response
        
    except Exception as e:
        logger.warning(f"Elicitation failed: {e}")
        return "⚠️ Elicitation mode encountered an error. Please use traditional mode with a genre parameter for recommendations."

@mcp_elicitation.tool()
@trace_tool("MCP.build_personalized_watchlist")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def build_personalized_watchlist(context: Context) -> str:
    """
    Build a personalized watchlist using elicitation to understand user preferences.

    This tool asks users about their current mood, available time, and company
    to create a customized watchlist of movies.

    Args:
        context (Context): The user or session context for personalization.

    Returns:
        str: A formatted string containing a personalized watchlist.
    """
    logger.info("Building personalized watchlist with elicitation")
    
    try:
        from app.models.elicitation import WatchlistPreferences
        
        # Elicit watchlist preferences
        preferences = await context.elicit(
            "What kind of movie experience are you looking for?",
            WatchlistPreferences
        )
        
        if not preferences:
            return "No preferences provided. Here are some general recommendations..."
        
        # Build watchlist based on preferences
        movies = await _build_personalized_watchlist(preferences)
        response = _format_movie_list(movies, "personalized watchlist")
        
        return response
        
    except Exception as e:
        logger.warning(f"Watchlist elicitation failed: {e}")
        return "⚠️ Watchlist building encountered an error. Please try again later."

@mcp_elicitation.tool()
@trace_tool("MCP.compare_movies_elicitation")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def compare_movies_elicitation(context: Context) -> str:
    """
    Compare two movies using elicitation to understand what aspects to focus on.

    This tool asks users which movies they want to compare and what aspects
    they're most interested in (acting, plot, visuals, etc.).

    Args:
        context (Context): The user or session context for personalization.

    Returns:
        str: A formatted string containing a detailed movie comparison.
    """
    logger.info("Comparing movies with elicitation")
    
    try:
        from app.models.elicitation import MovieComparison
        
        # Elicit comparison criteria
        comparison = await context.elicit(
            "Which movies would you like to compare and what aspects interest you?",
            MovieComparison
        )
        
        if not comparison:
            return "No comparison criteria provided. Please specify movies and aspects to compare."
        
        # Perform comparison
        result = await _compare_movies(comparison)
        return result
        
    except Exception as e:
        logger.warning(f"Movie comparison elicitation failed: {e}")
        return "⚠️ Movie comparison encountered an error. Please try again later."

# Helper functions for elicitation-based tools
async def _get_movies_by_preferences(preferences: UserPreferences) -> List[Movie]:
    """Get movies based on user preferences"""
    all_movies = await movie_service.get_all_movies()
    filtered_movies = []
    
    for movie in all_movies:
        # Filter by genres
        if preferences.preferred_genres:
            # Split comma-separated string into list
            preferred_genres = [genre.strip().lower() for genre in preferences.preferred_genres.split(',') if genre.strip()]
            if not any(genre in [g.lower() for g in movie.genres] for genre in preferred_genres):
                continue
        
        # Filter by duration
        if preferences.max_duration_minutes < 300 and movie.duration > preferences.max_duration_minutes:
            continue
        
        # Filter by rating
        if preferences.min_rating != "G":
            try:
                min_rating_enum = Rating(preferences.min_rating.upper())
                if movie.rating.value < min_rating_enum.value:
                    continue
            except ValueError:
                pass
        
        # Filter by decade
        if preferences.preferred_decade != "Any":
            movie_year = movie.release_date.year
            decade_start = int(preferences.preferred_decade.replace("s", "0"))
            if not (decade_start <= movie_year < decade_start + 10):
                continue
        
        filtered_movies.append(movie)
    
    # Sort by rating and return top results
    filtered_movies.sort(key=lambda x: x.average_rating, reverse=True)
    return filtered_movies[:10]

def _format_movie_list(movies: List[Movie], title: str) -> str:
    """Format a list of movies into a readable string"""
    response = f"Here are the {title}:\n\n"
    for movie in movies:
        response += f"🎬 {movie.title}\n"
        response += f"📝 {movie.description}\n"
        response += f"⭐ Rating: {movie.rating}\n"
        response += f"🎭 Genres: {', '.join(movie.genres)}\n"
        if movie.imdb_rating:
            response += f"📊 IMDB Rating: {movie.imdb_rating}/10\n"
        response += "\n"
    return response

async def _build_personalized_watchlist(preferences) -> List[Movie]:
    """Build a personalized watchlist based on preferences"""
    all_movies = await movie_service.get_all_movies()
    filtered_movies = []
    
    for movie in all_movies:
        # Filter by mood and time constraints
        if preferences.time_available and "2 hours" in preferences.time_available.lower():
            if movie.duration > 120:
                continue
        
        # Filter by company preferences
        if preferences.company and "family" in preferences.company.lower():
            if movie.rating.value > 2:  # Avoid R-rated movies for family
                continue
        
        # Filter by preferred genres
        if preferences.preferred_genres:
            preferred_genres = [genre.strip().lower() for genre in preferences.preferred_genres.split(',') if genre.strip()]
            if not any(genre in [g.lower() for g in movie.genres] for genre in preferred_genres):
                continue
        
        # Filter by avoid genres
        if preferences.avoid_genres:
            avoid_genres = [genre.strip().lower() for genre in preferences.avoid_genres.split(',') if genre.strip()]
            if any(genre in [g.lower() for g in movie.genres] for genre in avoid_genres):
                continue
        
        filtered_movies.append(movie)
    
    # Sort by rating and return top results
    filtered_movies.sort(key=lambda x: x.average_rating, reverse=True)
    return filtered_movies[:8]

async def _compare_movies(comparison) -> str:
    """Compare two movies based on specified criteria"""
    # This is a simplified comparison - in a real app, you'd have more detailed data
    movie1 = await movie_service.get_by_title(comparison.movie1_title)
    movie2 = await movie_service.get_by_title(comparison.movie2_title)
    
    if not movie1 or not movie2:
        return "One or both movies not found. Please check the movie titles."
    
    response = f"🎬 Movie Comparison: {movie1.title} vs {movie2.title}\n\n"
    
    # Compare based on requested aspects
    aspects = [aspect.strip() for aspect in comparison.comparison_aspects.split(',') if aspect.strip()]
    
    for aspect in aspects:
        aspect_lower = aspect.lower()
        if "rating" in aspect_lower and comparison.include_ratings:
            response += f"⭐ Ratings:\n"
            response += f"  {movie1.title}: {movie1.rating} (IMDB: {movie1.imdb_rating or 'N/A'})\n"
            response += f"  {movie2.title}: {movie2.rating} (IMDB: {movie2.imdb_rating or 'N/A'})\n\n"
        
        elif "genre" in aspect_lower:
            response += f"🎭 Genres:\n"
            response += f"  {movie1.title}: {', '.join(movie1.genres)}\n"
            response += f"  {movie2.title}: {', '.join(movie2.genres)}\n\n"
        
        elif "duration" in aspect_lower:
            response += f"⏱️ Duration:\n"
            response += f"  {movie1.title}: {movie1.duration} minutes\n"
            response += f"  {movie2.title}: {movie2.duration} minutes\n\n"
    
    return response
