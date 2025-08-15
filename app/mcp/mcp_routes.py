from fastmcp import FastMCP, Context
import logging
from app.core.middleware import LoggingMiddleware, JWTAuthMiddleware, OriginValidationMiddleware
from app.core.lifespan import shared_lifespan
from app.services.movie_service import MovieService
from app.repositories.movie_repository import FileMovieRepository
from app.models.movie import Genre, Rating
from app.core.config import settings
import os
import asyncio
from functools import wraps
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.middleware import Middleware


logger = logging.getLogger("MCP Movie App")

# Initialize FastMCP
mcp = FastMCP(
    "MCP Movie App",
    # description="A movie recommendation and search service",
    version="1.0.0"
)

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

# Conditionally enable Arize Phoenix instrumentation
# if settings.ENABLE_ARIZE:
#     tracer_provider = register(auto_instrument=True)
#     tracer = tracer_provider.get_tracer("mpc-server-movies")
# else:
#     tracer = None

def trace_tool(name):
    # def decorator(func):
    #     if settings.ENABLE_ARIZE and tracer:
    #         return tracer.tool(name=name)(func)
    #     return func
    # Return the original function if tracing is disabled or not available
    return lambda func: func

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.tool()
@trace_tool("MCP.suggest_movie")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def suggest_movie(genre: str, context: Context) -> str:
    """
    Suggest a list of movies based on a specified genre.

    This method uses the given genre to provide tailored movie suggestions.
    Ideal for users who are unsure what to watch and want recommendations 
    based on a specific genre (e.g., action, comedy, romance).

    Args:
        genre (str): The movie genre to base suggestions on.
        context (Context): The user or session context for personalization.

    Returns:
        str: A formatted string containing a list of suggested movies.
    """
    logger.info(f"Suggesting movie for genre: {genre}")
    try:
        # Convert string genre to Genre enum
        genre_enum = Genre(genre.capitalize())
        movies = await movie_service.get_by_genre(genre_enum)
        
        if not movies:
            return f"No movies found in the {genre} genre."
        
        # Format response with movie details
        response = f"Here are some great {genre} movies:\n\n"
        for movie in movies:
            response += f"🎬 {movie.title}\n"
            response += f"📝 {movie.description}\n"
            response += f"⭐ Rating: {movie.rating}\n"
            response += f"🎭 Genres: {', '.join(movie.genres)}\n"
            if movie.imdb_rating:
                response += f"📊 IMDB Rating: {movie.imdb_rating}/10\n"
            response += "\n"
        
        return response
    except ValueError:
        return f"Invalid genre: {genre}. Please use one of: {', '.join(g.value for g in Genre)}"

@mcp.tool()
@trace_tool("MCP.get_top_movies")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def get_top_movies(context: Context, rating: str = None) -> str:
    """
    Retrieve top-rated movies, optionally filtered by a specific rating.

    This method fetches the highest-rated movies, with an optional filter 
    for a specific rating category (e.g., PG, R). It’s useful for users 
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
        
        # Format response with movie details
        response = "Here are the top movies:\n\n"
        for movie in movies:
            response += f"🎬 {movie.title}\n"
            response += f"📝 {movie.description}\n"
            response += f"⭐ Rating: {movie.rating}\n"
            response += f"🎭 Genres: {', '.join(movie.genres)}\n"
            if movie.imdb_rating:
                response += f"📊 IMDB Rating: {movie.imdb_rating}/10\n"
            response += "\n"
        
        return response
    except ValueError:
        return f"Invalid rating: {rating}. Please use one of: {', '.join(r.value for r in Rating)}"

@mcp.tool()
@trace_tool("MCP.find_movies_title_cast")
@with_timeout(settings.MCP_TOOL_TIMEOUT)
async def find_movies_title_cast(title: str, cast: str, context: Context) -> str:
    """
    Search for movies by  title or cast only.

    This method searches across movie titles and cast members to match the input query.

    Args:
        title (str): The search keyword or phrase can be title of movie.
        cast (str): The search keyword or phrase can be cast member.
        context (Context): The user or session context for personalization.

    Returns:
        str: A formatted string with a list of movies matching the query.
    """
    logger.info(f"Searching movies with title: {title} and cast: {cast}")
    movies = await movie_service.search_movies(title+" "+cast)
    
    if not movies:
        return f"No movies found matching '{title}' and '{cast}'."
    
    # Format response with movie details
    response = f"Here are the movies matching '{title}' and '{cast}':\n\n"
    for movie in movies:
        response += f"🎬 {movie.title}\n"
        response += f"📝 {movie.description}\n"
        response += f"⭐ Rating: {movie.rating}\n"
        response += f"🎭 Genres: {', '.join(movie.genres)}\n"
        if movie.imdb_rating:
            response += f"📊 IMDB Rating: {movie.imdb_rating}/10\n"
        response += "\n"
    
    return response


# Create FastMCP app
# mcp_app = mcp.sse_app()
mcp_app = mcp.http_app(path="/mcp-server/mcp" , transport='streamable-http')


# Apply middleware to MCP app
mcp_app.add_middleware(LoggingMiddleware)
# Conditionally apply JWT middleware
logger.info(f"ENABLE_JWT: {settings.ENABLE_JWT}")
if settings.ENABLE_JWT:
    mcp_app.add_middleware(JWTAuthMiddleware)
mcp_app.add_middleware(OriginValidationMiddleware)


# Set lifespan context
# mcp_app.router.lifespan_context = shared_lifespan 