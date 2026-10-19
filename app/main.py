import fastapi as FAS
from pydantic import BaseModel

app = FAS.FastAPI()
app.title = "Obsluga"
app.version = "0.0.1"

class HealthResponse(BaseModel):
    status: str

@app.get("/api/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}