from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router

app = FastAPI(
    title="Tibeb AI Study Tutor API",
    description="Backend API for Amharic AI Study Tutor",
    version="0.1.0",
)


# Enable CORS for Flutter mobile client and local web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

