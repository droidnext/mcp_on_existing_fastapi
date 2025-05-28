from typing import List, Optional
from abc import ABC, abstractmethod
from app.repositories.base import BaseRepository
from app.models.movie import Movie, Review, Genre, Rating

class MovieRepository(ABC):
    @abstractmethod
    async def get_all_movies(self) -> List[Movie]:
        """Get all movies"""
        pass

    @abstractmethod
    async def get_movie(self, movie_id: str) -> Movie:
        """Get a specific movie by ID"""
        pass

    @abstractmethod
    async def get_by_genre(self, genre: Genre) -> List[Movie]:
        """Get movies by genre"""
        pass

    @abstractmethod
    async def get_by_rating(self, rating: Rating) -> List[Movie]:
        """Get movies by rating"""
        pass

    @abstractmethod
    async def get_top_rated(self, limit: int = 10) -> List[Movie]:
        """Get top rated movies"""
        pass

    @abstractmethod
    async def search_movies(self, query: str) -> List[Movie]:
        """Search movies by title, description, or cast"""
        pass

    @abstractmethod
    async def get_movie_reviews(self, movie_id: str) -> List[Review]:
        """Get all reviews for a movie"""
        pass

    @abstractmethod
    async def get_similar_movies(self, movie_id: str, limit: int = 5) -> List[Movie]:
        """Get similar movies based on genres and ratings"""
        pass

class FileMovieRepository(MovieRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._movies: List[Movie] = []
        self._load_movies()

    def _load_movies(self):
        """Load movies from JSON file"""
        import json
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self._movies = [Movie(**movie) for movie in data]
        except FileNotFoundError:
            self._movies = []
        except json.JSONDecodeError:
            self._movies = []

    async def get_all_movies(self) -> List[Movie]:
        return self._movies

    async def get_movie(self, movie_id: str) -> Movie:
        for movie in self._movies:
            if movie.id == movie_id:
                return movie
        raise ValueError(f"Movie not found: {movie_id}")

    async def get_by_genre(self, genre: Genre) -> List[Movie]:
        return [movie for movie in self._movies if genre in movie.genres]

    async def get_by_rating(self, rating: Rating) -> List[Movie]:
        return [movie for movie in self._movies if movie.rating == rating]

    async def get_top_rated(self, limit: int = 10) -> List[Movie]:
        sorted_movies = sorted(
            self._movies,
            key=lambda x: (x.average_rating or 0, x.imdb_rating or 0),
            reverse=True
        )
        return sorted_movies[:limit]

    async def search_movies(self, query: str) -> List[Movie]:
        query = query.lower()
        return [
            movie for movie in self._movies
            if query in movie.title.lower() or
               query in movie.description.lower() or
               any(query in actor.lower() for actor in movie.cast)
        ]

    async def get_movie_reviews(self, movie_id: str) -> List[Review]:
        movie = await self.get_movie(movie_id)
        return movie.reviews

    async def get_similar_movies(self, movie_id: str, limit: int = 5) -> List[Movie]:
        movie = await self.get_movie(movie_id)
        similar_movies = []
        
        for other_movie in self._movies:
            if other_movie.id == movie_id:
                continue
                
            # Calculate similarity score based on genres and rating
            genre_similarity = len(set(movie.genres) & set(other_movie.genres))
            rating_similarity = 1 if movie.rating == other_movie.rating else 0
            
            if genre_similarity > 0 or rating_similarity > 0:
                similar_movies.append((other_movie, genre_similarity + rating_similarity))
        
        # Sort by similarity score and return top matches
        similar_movies.sort(key=lambda x: x[1], reverse=True)
        return [movie for movie, _ in similar_movies[:limit]]

class DatabaseMovieRepository(MovieRepository):
    """Movie repository implementation using database storage"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_all_movies(self) -> List[Movie]:
        # Implementation for reading from database
        pass
    
    async def get_movie(self, movie_id: str) -> Movie:
        # Implementation for reading from database
        pass
    
    async def get_by_genre(self, genre: Genre) -> List[Movie]:
        # Implementation for reading from database
        pass
    
    async def get_by_rating(self, rating: Rating) -> List[Movie]:
        # Implementation for reading from database
        pass
    
    async def get_top_rated(self, limit: int = 10) -> List[Movie]:
        # Implementation for reading from database
        pass
    
    async def search_movies(self, query: str) -> List[Movie]:
        # Implementation for reading from database
        pass
    
    async def get_movie_reviews(self, movie_id: str) -> List[Review]:
        # Implementation for reading from database
        pass
    
    async def get_similar_movies(self, movie_id: str, limit: int = 5) -> List[Movie]:
        # Implementation for reading from database
        pass

class ExternalAPIMovieRepository(MovieRepository):
    """Movie repository implementation using external movie API (e.g., TMDB)"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def get_all_movies(self) -> List[Movie]:
        # Implementation for calling external API
        pass
    
    async def get_movie(self, movie_id: str) -> Movie:
        # Implementation for calling external API
        pass
    
    async def get_by_genre(self, genre: Genre) -> List[Movie]:
        # Implementation for calling external API
        pass
    
    async def get_by_rating(self, rating: Rating) -> List[Movie]:
        # Implementation for calling external API
        pass
    
    async def get_top_rated(self, limit: int = 10) -> List[Movie]:
        # Implementation for calling external API
        pass
    
    async def search_movies(self, query: str) -> List[Movie]:
        # Implementation for calling external API
        pass
    
    async def get_movie_reviews(self, movie_id: str) -> List[Review]:
        # Implementation for calling external API
        pass
    
    async def get_similar_movies(self, movie_id: str, limit: int = 5) -> List[Movie]:
        # Implementation for calling external API
        pass 