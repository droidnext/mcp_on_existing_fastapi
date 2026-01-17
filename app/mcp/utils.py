"""
Utility functions for MCP routes.
"""
from typing import List
from app.models.movie import Movie


def format_movie_list(movies: List[Movie], title: str = "movies") -> str:
    """
    Format a list of movies into a readable string.

    Args:
        movies: List of Movie objects to format
        title: Title prefix for the formatted list

    Returns:
        str: Formatted string containing movie details
    """
    if not movies:
        return f"No {title} found."

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


def format_movie_comparison(movie1: Movie, movie2: Movie, aspects: List[str], include_ratings: bool) -> str:
    """
    Format a comparison between two movies.

    Args:
        movie1: First movie to compare
        movie2: Second movie to compare
        aspects: List of aspects to compare (e.g., ['rating', 'genre', 'duration'])
        include_ratings: Whether to include rating information

    Returns:
        str: Formatted comparison string
    """
    response = f"🎬 Movie Comparison: {movie1.title} vs {movie2.title}\n\n"

    for aspect in aspects:
        aspect_lower = aspect.strip().lower()
        if "rating" in aspect_lower and include_ratings:
            response += "⭐ Ratings:\n"
            response += f"  {movie1.title}: {movie1.rating} (IMDB: {movie1.imdb_rating or 'N/A'})\n"
            response += f"  {movie2.title}: {movie2.rating} (IMDB: {movie2.imdb_rating or 'N/A'})\n\n"
        elif "genre" in aspect_lower:
            response += "🎭 Genres:\n"
            response += f"  {movie1.title}: {', '.join(movie1.genres)}\n"
            response += f"  {movie2.title}: {', '.join(movie2.genres)}\n\n"
        elif "duration" in aspect_lower:
            response += "⏱️ Duration:\n"
            response += f"  {movie1.title}: {movie1.duration} minutes\n"
            response += f"  {movie2.title}: {movie2.duration} minutes\n\n"

    return response
