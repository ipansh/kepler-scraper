from src import scraper
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()
app.include_router(scraper.router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )