"""
Elicitation response models for the movie recommendation system.
These dataclasses define the structure of user responses during elicitation.
FastMCP elicitation only supports primitive types: string, boolean, integer, number
No Optional types allowed - all fields must be primitive.
"""

from dataclasses import dataclass

@dataclass
class UserPreferences:
    """User preferences for movie recommendations - using only primitive types"""
    preferred_genres: str  # Comma-separated string instead of List[str]
    max_duration_minutes: int = 180  # Default to 3 hours instead of Optional[int]
    min_rating: str = "G"  # Default to G instead of Optional[str]
    include_foreign_films: bool = True
    preferred_decade: str = "Any"  # Default to "Any" instead of Optional[str]
    mood: str = "Any"  # Default to "Any" instead of Optional[str]

@dataclass
class RecommendationFeedback:
    """User feedback on recommendations - using only primitive types"""
    liked_movies: str  # Comma-separated string instead of List[str]
    disliked_movies: str  # Comma-separated string instead of List[str]
    additional_preferences: str = ""  # Empty string instead of Optional[str]
    rating_accuracy: int = 3  # Default to 3 instead of Optional[int] (1-5 scale)

@dataclass
class MovieSearchCriteria:
    """Criteria for searching movies - using only primitive types"""
    title_keywords: str = ""  # Empty string instead of Optional[str]
    director: str = ""  # Empty string instead of Optional[str]
    cast_member: str = ""  # Empty string instead of Optional[str]
    year_range: str = ""  # Empty string instead of Optional[str]
    min_imdb_rating: float = 0.0  # Default to 0.0 instead of Optional[float]
    max_duration: int = 300  # Default to 5 hours instead of Optional[int]

@dataclass
class WatchlistPreferences:
    """Preferences for building a watchlist - using only primitive types"""
    mood: str  # e.g., "feeling adventurous", "want something relaxing"
    time_available: str  # e.g., "2 hours", "90 minutes", "all evening"
    company: str  # e.g., "alone", "family", "date night", "friends"
    preferred_genres: str = ""  # Empty string instead of Optional[str]
    avoid_genres: str = ""  # Empty string instead of Optional[str]

@dataclass
class MovieComparison:
    """Criteria for comparing movies - using only primitive types"""
    movie1_title: str
    movie2_title: str
    comparison_aspects: str  # Comma-separated string instead of List[str]
    include_ratings: bool = True
    include_reviews: bool = True

@dataclass
class PersonalizedRecommendation:
    """Detailed preferences for personalized recommendations - using only primitive types"""
    favorite_movies: str  # Comma-separated string instead of List[str]
    least_favorite_movies: str  # Comma-separated string instead of List[str]
    preferred_directors: str = ""  # Empty string instead of Optional[str]
    preferred_actors: str = ""  # Empty string instead of Optional[str]
    avoid_content: str = ""  # Empty string instead of Optional[str]
    streaming_preferences: str = ""  # Empty string instead of Optional[str]
