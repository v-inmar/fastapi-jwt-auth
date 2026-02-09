from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


# ==== CORS SETTINGS FOR DEVELOPMENT ONLY ==== #
# ==== NOT GOOD FOR PRODUCTION ==== #
DEV_ORIGINS = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://0.0.0.0:5000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)





from app.api.auth import router as auth_router
from app.api.protected import router as protected_router

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(protected_router, prefix="/api/protected", tags=["Protected"])
