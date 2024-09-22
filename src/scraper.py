from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import logging
import time
import datetime
import pandas as pd
from src import classifieds
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from google.cloud import storage

service_account_key_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
gcs_client = storage.Client.from_service_account_json(service_account_key_path)
bucket = gcs_client.bucket('kleineinzeigen')

security = HTTPBasic()

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
service = Service(os.environ.get("CHROMEDRIVER_PATH"))
selenium_driver = webdriver.Chrome(service=service,
                                   options=chrome_options)

username = os.environ['SCRAPER_USERNAME']
password = os.environ['SCRAPER_PASSWORD']

#local testing
#selenium_driver = webdriver.Chrome()

logging.basicConfig(level=logging.INFO, format='%(levelname)s:     %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

def get_current_minute():
    current_minute = datetime.datetime.now().minute
    if current_minute < 20:
        return 0
    elif current_minute < 40:
        return 20
    else:
        return 40

@router.get("/health")
def health_check():
    return "OK"

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticates the user based on HTTP Basic auth."""
    correct_username = username
    correct_password = password  

    if not (credentials.username == correct_username and credentials.password == correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@router.get('/check_recent_listings', dependencies=[Depends(get_current_username)])
def check_recent_listings():
    output_list = classifieds.scrape_kleinanzeigen(selenium_driver)
    print('LISTINGS:')
    print(output_list)
    return output_list

@router.post('/scrape_listings_info', dependencies=[Depends(get_current_username)])
def scrape_listings_info(request_dict: dict):
    print(f'Received the request: {request_dict}')
    request_list = request_dict['urls']
    #temporary for testing
    request_list = request_list[0:5]
    print(f'Parsed to list: {request_list}')
    current_hour = int(time.localtime().tm_hour)
    current_date = datetime.date.today()
    metric_list = ['id','scraped_date','wohnfläche','zimmer','schlafzimmer','badezimmer',
                    'warmmiete','kaution/genoss.-anteile','etage','nebenkosten','heizkosten',
                    'wohnungstyp','verfügbarab','online-besichtigung','tauschangebot','miete',
                    'zipcode','district','url']
    master_df = pd.DataFrame()
    for scraped_url in request_list:
        print(f'Input URL: {scraped_url}')
        new_listing = classifieds.listing_url_to_dictionary(selenium_driver, scraped_url)
        try:
            new_listing = {key: new_listing[key] for key in metric_list}
            master_df = pd.concat([master_df, pd.DataFrame(new_listing, index = [0])]).reset_index().drop(columns = ['index'])
        except:
            pass
    master_df = master_df.rename(columns ={
                                'wohnfläche': 'wohnflache',
                                'kaution/genoss.-anteile': 'kaution',
                                'verfügbarab': 'verfugbarab',
                                'online-besichtigung': 'online_besichtigung',
                                })
    master_df = master_df.drop_duplicates(subset = ['id'])
    print(master_df.shape)
    master_df.to_csv(f'gs://kleinanzeigen-rent-listings/{str(current_date)}-{str(current_hour)}-{str(get_current_minute())}.csv')
    del master_df
    return 'Action triggered!'