import base64
import json
import logging
import socket
import threading
import time
from urllib.parse import urlparse

import httpx
from cachetools import TTLCache
from fastapi import HTTPException, Request
from jose import ExpiredSignatureError, JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("App")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP requests with timing and status codes."""
    
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        
        # Generate request ID for tracing
        request_id = request.headers.get("X-Request-ID") or f"req-{int(time.time() * 1000)}"
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            duration = time.time() - start
            
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s - "
                f"Request-ID: {request_id}"
            )
            return response
        except Exception as e:
            duration = time.time() - start
            logger.error(
                f"{request.method} {request.url.path} - "
                f"Error: {type(e).__name__} - "
                f"Duration: {duration:.3f}s - "
                f"Request-ID: {request_id}",
                exc_info=True,
            )
            raise

class OriginValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.allowed_hosts = settings.ALLOWED_HOSTS

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("Origin")
        if origin:
            try:
                parsed_origin = urlparse(origin)
                hostname = parsed_origin.hostname

                # Skip validation for allowed hosts
                if hostname in self.allowed_hosts:
                    return await call_next(request)

                # Validate hostname by resolving IP
                try:
                    ip = socket.gethostbyname(hostname)
                    # Check if IP is private/local
                    if ip.startswith(("127.", "10.", "172.16.", "192.168.")):
                        raise HTTPException(
                            status_code=403,
                            detail="Private IP addresses are not allowed",
                        )
                except socket.gaierror:
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid hostname",
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=403,
                    detail=f"Invalid origin: {str(e)}",
                )

        return await call_next(request)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication Middleware with header-first validation.
    
    Validates JWT tokens by:
    1. Reading token header to get 'alg', 'typ', 'jku'
    2. Using 'alg' from header (if present), falling back to config default
    3. Validating token type is 'JWT'
    4. Getting verification key:
       - If 'jku' is present: fetch public keys from JWKS URL
       - Otherwise: use configured secret key from config (not from header for security)
    5. Caching JWKS responses for 1 hour by default
    
    Note: Secret key is always read from config/environment, never from JWT header (security best practice).
    """

    # Class-level cache for JWKS responses (shared across all instances)
    # Cache: maxsize=100 JWKS URLs, ttl=3600 seconds (1 hour = default)
    _jwks_cache: TTLCache[str, dict] = TTLCache(maxsize=100, ttl=3600)
    _cache_lock = threading.Lock()

    def __init__(self, app, jwks_cache_ttl: int = 3600):
        """
        Initialize JWT Auth Middleware.
        
        Args:
            app: FastAPI application instance
            jwks_cache_ttl: Time-to-live for JWKS cache in seconds (default: 3600 = 1 hour)
                            Note: Only the first instance's TTL is used (class-level cache)
        """
        super().__init__(app)
        # Allowed algorithms from config (validates token header 'alg' against this list)
        self.allowed_algorithms = settings.JWT_ALLOWED_ALGORITHMS
        # Default algorithm from config (used if not specified in token header)
        self.default_algorithm = settings.JWT_ALGORITHM
        # Default secret key from config (used if not using JWKS)
        self.default_secret_key = settings.JWT_SECRET_KEY
        self.allowed_token_types = ["JWT", "at+JWT"]  # JWT or Access Token + JWT
        
        # Update cache TTL if different from default (only affects new cache initialization)
        # For existing cache, TTL is set at class definition
        if jwks_cache_ttl != 3600:
            with self._cache_lock:
                self._jwks_cache = TTLCache(maxsize=100, ttl=jwks_cache_ttl)
                logger.info(f"JWKS cache initialized with TTL: {jwks_cache_ttl}s")

    @staticmethod
    def decode_jwt_header(token: str) -> dict:
        """
        Decode JWT header without verification.
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Decoded header containing alg, typ, jku, etc.
        """
        try:
            # JWT format: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")

            # Decode header (base64url decode)
            header_data = parts[0]
            # Add padding if needed
            padding = 4 - len(header_data) % 4
            if padding != 4:
                header_data += "=" * padding

            header_bytes = base64.urlsafe_b64decode(header_data)
            header = json.loads(header_bytes.decode("utf-8"))
            return header
        except Exception as e:
            logger.error(f"Failed to decode JWT header: {e}")
            raise HTTPException(status_code=401, detail="Invalid token format")

    async def fetch_jwks(self, jku: str) -> dict:
        """
        Fetch JSON Web Key Set from JWKS URL with caching.
        
        JWKS responses are cached for 1 hour (default) to reduce network requests
        and improve performance. Cache uses TTLCache for automatic expiration.
        
        Args:
            jku: JSON Web Key Set URL
            
        Returns:
            dict: JWKS containing public keys
        """
        try:
            # Check cache first (thread-safe read)
            with self._cache_lock:
                if jku in self._jwks_cache:
                    logger.debug(f"JWKS cache hit for: {jku[:50]}...")
                    return self._jwks_cache[jku]

            # Validate URL scheme (only allow https in production)
            parsed = urlparse(jku)
            if settings.ENV == "prod" and parsed.scheme != "https":
                logger.error(f"Rejected non-HTTPS JWKS URL in production: {jku[:50]}...")
                raise HTTPException(
                    status_code=401, detail="Invalid JWKS URL scheme"
                )
            if parsed.scheme not in ["https", "http"]:
                raise HTTPException(
                    status_code=401, detail="Invalid JWKS URL scheme"
                )

            # Fetch JWKS from URL
            logger.info(f"Fetching JWKS from: {parsed.hostname or 'unknown'} (cache miss)")
            
            # Use connection pooling for better performance
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                follow_redirects=True,
            ) as client:
                response = await client.get(jku)
                response.raise_for_status()
                jwks_data = response.json()

            # Store in cache (thread-safe write)
            with self._cache_lock:
                self._jwks_cache[jku] = jwks_data
                logger.debug(f"JWKS cached for: {jku} (TTL: {self._jwks_cache.ttl}s)")

            return jwks_data

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch JWKS from {jku}: {e}")
            raise HTTPException(
                status_code=401, detail=f"Failed to fetch JWKS: {str(e)}"
            )

    async def get_verification_key(self, token: str, header: dict):
        """
        Get the appropriate key for token verification.
        
        If 'jku' is present, fetches public keys from JWKS URL.
        Otherwise, uses configured secret key.
        
        Args:
            token: JWT token
            header: Decoded JWT header
            
        Returns:
            str or dict: Secret key string (for HS256) or key dict (for RS256/ES256 from JWKS)
        """
        # If jku (JSON Web Key Set URL) is present, fetch public keys
        if "jku" in header:
            logger.info(f"Fetching JWKS from: {header['jku']}")
            jwks = await self.fetch_jwks(header["jku"])

            # Extract key ID from token header
            kid = header.get("kid")
            if not kid:
                raise HTTPException(
                    status_code=401, detail="Token missing 'kid' header for JWKS"
                )

            # Find matching key in JWKS
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    # Return key dict for RS256/ES256 (python-jose will handle it)
                    # Note: For production, you may want to cache JWKS keys
                    return key

            raise HTTPException(
                status_code=401, detail=f"Key with kid '{kid}' not found in JWKS"
            )

        # Fall back to configured secret key for symmetric algorithms (HS256/HS384/HS512)
        # Secret key comes from config, not JWT header (for security reasons)
        # Secret key is only required if not using JWKS (no 'jku' in header)
        if not self.default_secret_key:
            raise HTTPException(
                status_code=401,
                detail="JWT secret key not configured and no JWKS URL ('jku') provided in token header. "
                       "Either configure JWT_SECRET_KEY or use tokens with 'jku' header for public key validation.",
            )
        return self.default_secret_key

    async def dispatch(self, request: Request, call_next):
        """Process request with JWT authentication."""
        # Exclude public paths
        if request.url.path in ["/docs", "/openapi.json", "/", "/mcp/docs"]:
            return await call_next(request)

        # Extract token from Authorization header
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(
                status_code=401, detail="Missing or invalid Authorization header"
            )

        # Extract token safely
        try:
            token = auth.split(" ", 1)[1]
        except IndexError:
            raise HTTPException(
                status_code=401, detail="Invalid Authorization header format"
            )

        # Validate token format
        if not token or len(token) < 10:
            raise HTTPException(
                status_code=401, detail="Invalid token format"
            )

        try:
            # Decode and validate JWT header
            header = self.decode_jwt_header(token)

            # Get algorithm from JWT header, fall back to config if not present
            alg = header.get("alg")
            if not alg:
                # If no algorithm in header, use default from config
                alg = self.default_algorithm
                logger.debug(f"No 'alg' in JWT header, using default from config: {alg}")
            
            # Validate algorithm is in allowed list
            if alg not in self.allowed_algorithms:
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid algorithm '{alg}'. Allowed: {self.allowed_algorithms}",
                )

            # Validate token type
            typ = header.get("typ")
            if typ and typ not in self.allowed_token_types:
                logger.warning(f"Token type '{typ}' not in allowed types: {self.allowed_token_types}")

            # Get verification key (from JWKS or secret)
            verification_key = await self.get_verification_key(token, header)

            # Decode and verify token
            # python-jose handles both string secrets (HS256) and dict keys (RS256/ES256 from JWKS)
            payload = jwt.decode(
                token,
                verification_key,
                algorithms=[alg],
                options={"verify_exp": True, "verify_signature": True},
            )

            # Store user payload in request state (sanitize for logging)
            request.state.user = payload
            user_id = payload.get('sub', 'unknown')
            # Don't log full payload in production (security)
            if settings.ENV == "prod":
                logger.debug(f"JWT validated successfully for user: {user_id[:20]}...")
            else:
                logger.debug(f"JWT validated successfully for user: {user_id}")

        except ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except JWTError as e:
            # Don't leak sensitive error details in production
            error_msg = "Invalid token" if settings.ENV == "prod" else f"Invalid token: {str(e)}"
            logger.error(f"JWT validation error: {type(e).__name__}")
            raise HTTPException(status_code=401, detail=error_msg)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during JWT validation: {type(e).__name__}", exc_info=True)
            error_msg = "Token validation failed" if settings.ENV == "prod" else f"Token validation failed: {str(e)}"
            raise HTTPException(status_code=401, detail=error_msg)

        return await call_next(request) 