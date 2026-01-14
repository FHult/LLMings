"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import session, providers, files, ollama, config, archetypes, system, templates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting LLMings API...")

    # Validate and log configuration
    settings.log_configuration_status()

    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully!")

    yield

    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="LLMings API",
    description="Multi-AI council with consensus building",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(session.router, prefix="/api", tags=["sessions"])
app.include_router(providers.router, prefix="/api", tags=["providers"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(ollama.router, prefix="/api", tags=["ollama"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(archetypes.router, prefix="/api", tags=["archetypes"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(templates.router, prefix="/api", tags=["templates"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "LLMings API",
        "version": "0.1.0",
        "status": "running",
        "configured_providers": settings.configured_providers,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
