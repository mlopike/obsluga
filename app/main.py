from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.routers import auth, equipment, tickets

app = FastAPI()
app.title = "Obsluga"
app.version = "0.0.1"


class HealthResponse(BaseModel):
    status: str


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(equipment.router, prefix="/api/equipment", tags=["equipment"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])

app.mount("/", StaticFiles(directory="static", html=True))
