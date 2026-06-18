from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes import auth, users
from app.database import engine, Base
from app.utils import limiter  # Import from utils

# Automatically create database tables
Base.metadata.create_all(bind=engine)

# 1. Initialize the Rate Limiter using the client's IP address
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="JWT Auth Service",
    description="A simple FastAPI service for JWT-based authentication",
    version="1.0.0"
)

# 2. Attach the limiter to the app state and handle "Too Many Requests" errors
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 3. CORS Middleware: Restrict access to trusted domains
# (Change allow_origins to your frontend URL in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Security Headers Middleware: Protects against common web attacks
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/health", tags=["System"])
def health_check():
    """Service health check endpoint."""
    return {"status": "healthy"}