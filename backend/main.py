from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.enrich_router import enrich
import uvicorn

app = FastAPI(title="Finding Tickers")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# test endpoint
@app.get("/test", tags=["test"])
def test_api_endpoint():
    return {"message": "This is a test endpoint and it's working"}

# enrich endpoint
app.include_router(enrich)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)