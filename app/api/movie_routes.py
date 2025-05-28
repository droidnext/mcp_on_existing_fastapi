from fastapi import APIRouter, HTTPException, Request, Depends, Query
from typing import List, Optional
from app.services.movie_service import MovieService
from app.repositories.movie_repository import FileMovieRepository
from app.models.movie import Movie, Genre, Rating
from app.exceptions.movie_exceptions import MovieError, MovieNotFoundError
import os

router = APIRouter(prefix="/movies", tags=["movies"])

# Dependency to get movie service
async def get_movie_service():
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "movies.json")
    repository = FileMovieRepository(file_path)
    return MovieService(repository)

@router.get("/", response_model=List[Movie])
async def list_movies(
    service: MovieService = Depends(get_movie_service),
    search: Optional[str] = None
):
    """Get all movies with optional search"""
    if search:
        return await service.search_movies(search)
    return await service.get_all_movies()

@router.get("/by-genre/{genre}", response_model=List[Movie])
async def get_movies_by_genre(
    genre: Genre,
    service: MovieService = Depends(get_movie_service)
):
    """Get movies by genre"""
    return await service.get_by_genre(genre)

@router.get("/by-rating/{rating}", response_model=List[Movie])
async def get_movies_by_rating(
    rating: Rating,
    service: MovieService = Depends(get_movie_service)
):
    """Get movies by rating"""
    return await service.get_by_rating(rating)

@router.get("/top-rated", response_model=List[Movie])
async def get_top_rated(
    limit: int = Query(default=10, ge=1, le=50),
    service: MovieService = Depends(get_movie_service)
):
    """Get top rated movies"""
    return await service.get_top_rated(limit)

@router.get("/{movie_id}", response_model=Movie)
async def get_movie(
    movie_id: str,
    service: MovieService = Depends(get_movie_service)
):
    """Get a specific movie by ID"""
    try:
        return await service.get_movie(movie_id)
    except MovieNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{movie_id}/similar", response_model=List[Movie])
async def get_similar_movies(
    movie_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    service: MovieService = Depends(get_movie_service)
):
    """Get similar movies"""
    try:
        return await service.get_similar_movies(movie_id, limit)
    except MovieNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) 