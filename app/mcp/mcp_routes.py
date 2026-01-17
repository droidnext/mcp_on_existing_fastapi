import asyncio
import json
import logging
import os
import time
from functools import wraps

from fastmcp import FastMCP
from fastmcp.server import Context
from fastmcp.server.middleware import Middleware, MiddlewareContext
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from app.core.config import settings
from app.core.middleware import (
    JWTAuthMiddleware,
    LoggingMiddleware,
    OriginValidationMiddleware,
)
from app.models.movie import Genre, Rating
from app.mcp.utils import format_movie_list
from app.repositories.movie_repository import FileMovieRepository
from app.services.movie_service import MovieService


logger = logging.getLogger("MCP Movie App")

# Initialize FastMCP
mcp = FastMCP(
    "MCP Movie App",
    version="1.0.0"
)


# FastMCP middleware for MCP protocol-level operations
class MCPLoggingMiddleware(Middleware):
    """Log MCP protocol-level operations."""
    
    async def on_message(self, context: MiddlewareContext, call_next):
        """Log all MCP messages."""
        logger.info(f"MCP message: {context.method} from {context.source}")
        try:
            result = await call_next(context)
            logger.info(f"MCP message completed: {context.method}")
            return result
        except Exception as e:
            logger.error(f"MCP message failed: {context.method} - {e}")
            raise
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Log tool calls with timing."""
        start = time.time()
        tool_name = context.message.params.get("name", "unknown")
        logger.info(f"Calling tool: {tool_name}")
        try:
            result = await call_next(context)
            duration = time.time() - start
            logger.info(f"Tool {tool_name} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"Tool {tool_name} failed after {duration:.3f}s: {e}")
            raise


# Add FastMCP middleware to the mcp instance (before creating http_app)
mcp.add_middleware(MCPLoggingMiddleware())

# Initialize movie service
file_path = os.path.join(os.path.dirname(__file__), "..", "data", "movies.json")
movie_repository = FileMovieRepository(file_path)
movie_service = MovieService(movie_repository)

def with_timeout(timeout_seconds):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error(f"Tool {func.__name__} timed out after {timeout_seconds} seconds")
                return f"Operation timed out after {timeout_seconds} seconds. Please try again."
        return wrapper
    return decorator

def trace_tool(name):
    return lambda func: func

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.tool()
@trace_tool("MCP.suggest_movie")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def suggest_movie(genre: str, context: Context = None) -> str:
    """
    Suggest movies based on genre.

    This tool provides movie recommendations based on the specified genre.

    Args:
        genre (str): The movie genre to base suggestions on.
        context (Context): The user or session context for personalization.

    Returns:
        str: A formatted string containing movie suggestions.
    """
    logger.info(f"Starting movie suggestion with genre: {genre}")

    try:
        genre_enum = Genre(genre.capitalize())
        movies = await movie_service.get_by_genre(genre_enum)

        if not movies:
            return f"No movies found in the {genre} genre."

        return format_movie_list(movies, "movie recommendations")
    except ValueError:
        return f"Invalid genre: {genre}. Please use one of: {', '.join(g.value for g in Genre)}"

@mcp.tool()
@trace_tool("MCP.get_top_movies")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def get_top_movies(context: Context, rating: str = None) -> str:
    """
    Retrieve top-rated movies, optionally filtered by a specific rating.

    This method fetches the highest-rated movies, with an optional filter 
    for a specific rating category (e.g., PG, R). It's useful for users 
    interested in critically acclaimed or popular content.

    Args:
        context (Context): The user or session context for personalization.
        rating (str, optional): Rating category to filter top movies by.

    Returns:
        str: A formatted string containing a list of top-rated movies.
    """
    logger.info(f"Getting top movies with rating filter: {rating}")
    try:
        if rating:
            # Convert string rating to Rating enum
            rating_enum = Rating(rating.upper())
            movies = await movie_service.get_by_rating(rating_enum)
        else:
            movies = await movie_service.get_top_rated(limit=5)
        
        if not movies:
            rating_text = f" with rating {rating}" if rating else ""
            return f"No movies found{rating_text}."

        return format_movie_list(movies, "top movies")
    except ValueError:
        return f"Invalid rating: {rating}. Please use one of: {', '.join(r.value for r in Rating)}"

@mcp.tool()
@trace_tool("MCP.find_movies_title_cast")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def find_movies_title_cast(title: str, cast: str, context: Context) -> str:
    """
    Search for movies by title or cast only.

    This method searches across movie titles and cast members to match the input query.

    Args:
        title (str): The search keyword or phrase can be title of movie.
        cast (str): The search keyword or phrase can be cast member.
        context (Context): The user or session context for personalization.

    Returns:
        str: A formatted string with a list of movies matching the query.
    """
    logger.info(f"Searching movies with title: {title} and cast: {cast}")
    movies = await movie_service.search_movies(f"{title} {cast}")

    if not movies:
        return f"No movies found matching '{title}' and '{cast}'."

    return format_movie_list(movies, f"movies matching '{title}' and '{cast}'")


# ============================================================================
# MCP Resources
# ============================================================================
# Resources allow servers to expose data that provides context to language models.
# See: https://modelcontextprotocol.io/specification/2025-11-25/server/resources

@mcp.resource("movie://database")
async def get_movie_database() -> str:
    """
    Get the entire movie database as a JSON resource.
    
    This resource provides access to all movie data in the system,
    which can be used by clients to provide context about available movies.
    """
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "movies.json")
    with open(file_path, "r") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)


@mcp.resource("movie://genres")
async def get_genres_list() -> str:
    """
    Get a list of all available movie genres.
    
    This resource provides a list of all genres in the database,
    useful for clients to understand what movie categories are available.
    """
    genres = [genre.value for genre in Genre]
    return json.dumps({"genres": genres}, indent=2)


@mcp.resource("movie://{movie_id}")
async def get_movie_by_id(movie_id: str) -> str:
    """
    Get a specific movie by ID.
    
    Args:
        movie_id: The unique identifier of the movie.
        
    This resource template allows accessing individual movies by their ID,
    following the MCP resource template pattern.
    """
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "movies.json")
    with open(file_path, "r") as f:
        movies = json.load(f)
    
    movie = next((m for m in movies if m.get("id") == movie_id), None)
    if not movie:
        return json.dumps({"error": f"Movie with ID {movie_id} not found"}, indent=2)
    
    return json.dumps(movie, indent=2)


# ============================================================================
# MCP Prompts
# ============================================================================
# Prompts allow servers to expose prompt templates to clients.
# See: https://modelcontextprotocol.io/specification/2025-11-25/server/prompts

@mcp.prompt()
async def movie_recommendation_prompt(
    genre: str,
    mood: str = "Any",
    max_duration: int = 180,
) -> list:
    """
    Get a prompt template for requesting movie recommendations.
    
    Args:
        genre: The movie genre to recommend (e.g., "Action", "Comedy", "Drama")
        mood: The desired mood or atmosphere (default: "Any")
        max_duration: Maximum movie duration in minutes (default: 180)
        
    This prompt provides a structured message that clients can use to ask
    for movie recommendations with specific criteria.
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"I'm looking for {genre} movie recommendations. "
                f"I'm in the mood for something {mood.lower()} and prefer "
                f"movies under {max_duration} minutes. "
                f"Can you help me find some great {genre} movies to watch?",
            },
        }
    ]


@mcp.prompt()
async def movie_comparison_prompt(
    movie1_title: str,
    movie2_title: str,
    comparison_aspects: str = "rating,genre,duration",
) -> list:
    """
    Get a prompt template for comparing two movies.
    
    Args:
        movie1_title: Title of the first movie to compare
        movie2_title: Title of the second movie to compare
        comparison_aspects: Comma-separated list of aspects to compare
                           (e.g., "rating,genre,duration")
        
    This prompt helps users compare two movies across different aspects.
    """
    aspects_list = [aspect.strip() for aspect in comparison_aspects.split(",")]
    aspects_text = ", ".join(aspects_list[:-1])
    if len(aspects_list) > 1:
        aspects_text += f", and {aspects_list[-1]}"
    else:
        aspects_text = aspects_list[0] if aspects_list else "various aspects"
    
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"Please compare '{movie1_title}' and '{movie2_title}' "
                f"based on the following aspects: {aspects_text}. "
                f"Help me understand the similarities and differences between "
                f"these two movies to help me decide which one to watch.",
            },
        }
    ]


@mcp.prompt()
async def movie_search_prompt(
    query: str,
    search_type: str = "title",
) -> list:
    """
    Get a prompt template for searching movies.
    
    Args:
        query: The search query (title, actor, or keyword)
        search_type: Type of search - "title", "cast", or "any" (default: "title")
        
    This prompt helps users search for movies by various criteria.
    """
    search_descriptions = {
        "title": "by title",
        "cast": "by actor or cast member",
        "any": "by title, cast, or description",
    }
    search_desc = search_descriptions.get(search_type, "by title")
    
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"I'm searching for movies {search_desc} using the query: '{query}'. "
                f"Can you help me find movies that match this search? "
                f"Please provide details about any matching movies you find.",
            },
        }
    ]


def apply_http_middleware(mcp_app):
    """
    Apply HTTP-level middleware to MCP FastAPI app.
    
    Note: These middleware work at the HTTP level (headers, requests, etc.)
    and must be applied to the FastAPI app instance, not the FastMCP instance.
    For MCP protocol-level middleware, use mcp.add_middleware() instead.
    """
    # HTTP request/response logging
    mcp_app.add_middleware(LoggingMiddleware)
    
    # Conditionally apply JWT middleware (requires HTTP Authorization header)
    logger.info(f"ENABLE_JWT: {settings.ENABLE_JWT}")
    if settings.ENABLE_JWT:
        mcp_app.add_middleware(JWTAuthMiddleware)
    
    # HTTP origin validation (requires HTTP Origin header)
    mcp_app.add_middleware(OriginValidationMiddleware(mcp_app))


# Create FastMCP app (FastMCP middleware is already added above)
# Transport options:
# - "streamable-http": HTTP-based transport for web APIs (default, recommended)
# - "stdio": Standard I/O transport for CLI/integrated applications
# mcp_app = mcp.http_app(path="/mcp", transport="stdio")  # Uncomment for stdio transport
mcp_app = mcp.http_app(path="/mcp", transport=settings.MCP_TRANSPORT)

# Apply HTTP-level middleware to the FastAPI app
apply_http_middleware(mcp_app) 