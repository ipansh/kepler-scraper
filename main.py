from src.routers import scraper
from fastapi import FastAPI
import uvicorn
import os


from selenium import webdriver
from selenium.webdriver.chrome.service import Service


from google.cloud import storage
import time
import datetime

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")

service = Service(os.environ.get("CHROMEDRIVER_PATH"))
options = webdriver.ChromeOptions()
selenium_driver = webdriver.Chrome(service=service, options=chrome_options)

app = FastAPI()
app.include_router(scraper.router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )