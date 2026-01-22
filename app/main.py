from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router

app = FastAPI(
    title="Modern E-commerce API",
    version="0.1.0",
)

# CORS Middleware (Allow All for Development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: replace with frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the E-commerce API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
