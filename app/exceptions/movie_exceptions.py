class MovieError(Exception):
    """Base exception for movie-related errors"""
    pass

class MovieNotFoundError(MovieError):
    """Raised when a movie is not found"""
    pass

class ShowNotFoundError(MovieError):
    """Raised when a show is not found"""
    pass

class NoSeatsAvailableError(MovieError):
    """Raised when no seats are available for booking"""
    pass

class InvalidBookingError(MovieError):
    """Raised when a booking request is invalid"""
    pass 