from typing import List, Optional
from app.repositories.movie_repository import MovieRepository
from app.models.movie import Movie, Review, Genre, Rating
from app.exceptions.movie_exceptions import MovieNotFoundError

class MovieService:
    def __init__(self, repository: MovieRepository):
        self.repository = repository
    
    async def get_all_movies(self) -> List[Movie]:
        """Get all movies"""
        return await self.repository.get_all_movies()
    
    async def get_movie(self, movie_id: str) -> Movie:
        """Get a specific movie by ID"""
        try:
            return await self.repository.get_movie(movie_id)
        except ValueError as e:
            raise MovieNotFoundError(str(e))
    
    async def get_by_genre(self, genre: Genre) -> List[Movie]:
        """Get movies by genre"""
        return await self.repository.get_by_genre(genre)
    
    async def get_by_rating(self, rating: Rating) -> List[Movie]:
        """Get movies by rating"""
        return await self.repository.get_by_rating(rating)
    
    async def get_top_rated(self, limit: int = 10) -> List[Movie]:
        """Get top rated movies"""
        return await self.repository.get_top_rated(limit)
    
    async def search_movies(self, query: str) -> List[Movie]:
        """Search movies by title, description, or cast"""
        return await self.repository.search_movies(query)
    
    async def get_movie_reviews(self, movie_id: str) -> List[Review]:
        """Get all reviews for a movie"""
        # Verify movie exists first
        await self.get_movie(movie_id)
        return await self.repository.get_movie_reviews(movie_id)
    
    async def get_similar_movies(self, movie_id: str, limit: int = 5) -> List[Movie]:
        """Get similar movies based on genres and ratings"""
        # First verify movie exists
        await self.get_movie(movie_id)
        return await self.repository.get_similar_movies(movie_id, limit) 