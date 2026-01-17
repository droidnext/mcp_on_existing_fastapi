"""
MCP Elicitation Routes for Movie Recommendation System

This module contains tools that use FastMCP elicitation for interactive
user input gathering. These tools provide personalized recommendations
by asking users about their preferences through structured forms.
"""

import logging
import os
from typing import List

from fastmcp import FastMCP
from fastmcp.server import Context

from app.core.config import settings
from app.models.elicitation import RecommendationFeedback, UserPreferences
from app.models.movie import Movie, Rating
from app.mcp.mcp_routes import trace_tool, with_timeout
from app.mcp.utils import format_movie_comparison, format_movie_list
from app.repositories.movie_repository import FileMovieRepository
from app.services.movie_service import MovieService

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
            UserPreferences,
        )

        if not preferences:
            return "No preferences provided. Here are some general recommendations..."

        # Use preferences to get recommendations
        movies = await _get_movies_by_preferences(preferences)
        response = format_movie_list(movies, "personalized recommendations")

        # Second elicitation: Get feedback for future improvements
        feedback = await context.elicit(
            "How did you like these recommendations?",
            RecommendationFeedback,
        )

        if feedback and feedback.liked_movies:
            # Split comma-separated string and take first 3
            liked_list = [
                movie.strip()
                for movie in feedback.liked_movies.split(",")
                if movie.strip()
            ]
            if liked_list:
                response += (
                    f"\n\n💡 Based on your feedback, we'll remember you liked: "
                    f"{', '.join(liked_list[:3])}"
                )
            elif feedback.rating_accuracy > 3:
                response += (
                    f"\n\n💡 Thank you for the positive feedback "
                    f"(rating: {feedback.rating_accuracy}/5)!"
                )

        return response

    except Exception as e:
        logger.warning(f"Elicitation failed: {e}")
        return (
            "⚠️ Elicitation mode encountered an error. "
            "Please use traditional mode with a genre parameter for recommendations."
        )

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
            WatchlistPreferences,
        )

        if not preferences:
            return "No preferences provided. Here are some general recommendations..."

        # Build watchlist based on preferences
        movies = await _build_personalized_watchlist(preferences)
        return format_movie_list(movies, "personalized watchlist")

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
            MovieComparison,
        )

        if not comparison:
            return (
                "No comparison criteria provided. "
                "Please specify movies and aspects to compare."
            )

        # Perform comparison
        return await _compare_movies(comparison)

    except Exception as e:
        logger.warning(f"Movie comparison elicitation failed: {e}")
        return "⚠️ Movie comparison encountered an error. Please try again later."

# Helper functions for elicitation-based tools
async def _get_movies_by_preferences(preferences: UserPreferences) -> List[Movie]:
    """Get movies based on user preferences."""
    all_movies = await movie_service.get_all_movies()
    filtered_movies = []

    for movie in all_movies:
        # Filter by genres
        if preferences.preferred_genres:
            preferred_genres = [
                genre.strip().lower()
                for genre in preferences.preferred_genres.split(",")
                if genre.strip()
            ]
            if not any(
                genre in [g.lower() for g in movie.genres] for genre in preferred_genres
            ):
                continue

        # Filter by duration
        if (
            preferences.max_duration_minutes < 300
            and movie.duration > preferences.max_duration_minutes
        ):
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

async def _build_personalized_watchlist(preferences) -> List[Movie]:
    """Build a personalized watchlist based on preferences."""
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
            preferred_genres = [
                genre.strip().lower()
                for genre in preferences.preferred_genres.split(",")
                if genre.strip()
            ]
            if not any(
                genre in [g.lower() for g in movie.genres] for genre in preferred_genres
            ):
                continue

        # Filter by avoid genres
        if preferences.avoid_genres:
            avoid_genres = [
                genre.strip().lower()
                for genre in preferences.avoid_genres.split(",")
                if genre.strip()
            ]
            if any(genre in [g.lower() for g in movie.genres] for genre in avoid_genres):
                continue

        filtered_movies.append(movie)

    # Sort by rating and return top results
    filtered_movies.sort(key=lambda x: x.average_rating, reverse=True)
    return filtered_movies[:8]

async def _compare_movies(comparison) -> str:
    """Compare two movies based on specified criteria."""
    movie1 = await movie_service.get_by_title(comparison.movie1_title)
    movie2 = await movie_service.get_by_title(comparison.movie2_title)

    if not movie1 or not movie2:
        return "One or both movies not found. Please check the movie titles."

    # Compare based on requested aspects
    aspects = [
        aspect.strip()
        for aspect in comparison.comparison_aspects.split(",")
        if aspect.strip()
    ]

    return format_movie_comparison(movie1, movie2, aspects, comparison.include_ratings)


# Create FastMCP elicitation app
# Transport options:
# - "streamable-http": HTTP-based transport for web APIs (default, recommended)
# - "stdio": Standard I/O transport for CLI/integrated applications
# mcp_elicitation_app = mcp_elicitation.http_app(path="/mcp/elicitation", transport="stdio")  # Uncomment for stdio transport
mcp_elicitation_app = mcp_elicitation.http_app(
    path="/mcp/elicitation", transport=settings.MCP_TRANSPORT
)
