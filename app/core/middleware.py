from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError, ExpiredSignatureError
import time
import logging
from app.core.config import settings
from urllib.parse import urlparse
import socket

logger = logging.getLogger("App")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(f"{request.method} {request.url.path} - {duration:.3f}s")
        return response

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
                            detail="Private IP addresses are not allowed"
                        )
                except socket.gaierror:
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid hostname"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=403,
                    detail=f"Invalid origin: {str(e)}"
                )
        
        return await call_next(request)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/docs", "/openapi.json", "/", "/mcp/docs"]:  # Exclude public paths
            return await call_next(request)

        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request.state.user = payload
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        return await call_next(request) 