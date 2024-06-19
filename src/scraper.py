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

#deployment
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

@router.get("/health")
def health_check():
    #selenium_driver.quit()
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

@router.post('/api/trigger', dependencies=[Depends(get_current_username)])
def trigger_action():
    print('The script is up and running!')
    current_hour = int(time.localtime().tm_hour)
    current_date = datetime.date.today()
    scraper_output_list = classifieds.scrape_ebay(selenium_driver)
    metric_list = ['id','scraped_date','wohnfläche','zimmer','schlafzimmer','badezimmer',
                    'warmmiete','kaution/genoss.-anteile','etage','nebenkosten','heizkosten',
                    'wohnungstyp','verfügbarab','online-besichtigung','tauschangebot','miete',
                    'zipcode','district','url']
    master_df = pd.DataFrame()
    for scraped_url in scraper_output_list:
        new_listing = classifieds.listing_url_to_dictionary(selenium_driver, scraped_url)
        print(new_listing['id'])
        new_listing = {key: new_listing[key] for key in metric_list}
        master_df = pd.concat([master_df, pd.DataFrame(new_listing, index = [0])]).reset_index().drop(columns = ['index'])
        del new_listing
        break
    master_df = master_df.drop_duplicates(subset = ['id'])
    #master_df['is_right_fit'] = master_df['is_right_fit'].fillna(0)
    print(master_df.head(4))
    master_df.to_csv(f'gs://kleineinzeigen/test_{str(current_date)}_{str(current_hour)}.csv')
    del master_df
    return 'Action triggered!'