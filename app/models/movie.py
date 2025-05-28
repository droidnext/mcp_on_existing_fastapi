from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

class Genre(str, Enum):
    ACTION = "Action"
    ADVENTURE = "Adventure"
    COMEDY = "Comedy"
    CRIME = "Crime"
    DRAMA = "Drama"
    FANTASY = "Fantasy"
    HORROR = "Horror"
    MYSTERY = "Mystery"
    ROMANCE = "Romance"
    SCIENCE_FICTION = "Science Fiction"
    THRILLER = "Thriller"

class Rating(str, Enum):
    G = "G"
    PG = "PG"
    PG_13 = "PG-13"
    R = "R"
    NC_17 = "NC-17"

class Review(BaseModel):
    id: str
    movie_id: str
    user_id: str
    rating: float = Field(ge=0, le=5)
    comment: str
    created_at: datetime
    helpful_votes: int = Field(ge=0)

class Movie(BaseModel):
    id: str
    title: str
    description: str
    duration: int = Field(gt=0)  # Duration in minutes
    genres: List[Genre]
    rating: Rating
    release_date: datetime
    director: str
    cast: List[str]
    reviews: List[Review] = []
    average_rating: float = Field(ge=0, le=5)
    total_reviews: int = Field(ge=0)
    poster_url: Optional[HttpUrl] = None
    trailer_url: Optional[HttpUrl] = None
    imdb_rating: Optional[float] = Field(None, ge=0, le=10)
    rotten_tomatoes_score: Optional[int] = Field(None, ge=0, le=100) 