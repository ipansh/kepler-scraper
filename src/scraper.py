from fastapi import APIRouter
import logging
import time
import datetime
import pandas as pd
from src import classifieds
import os


from selenium import webdriver
from selenium.webdriver.chrome.service import Service


from google.cloud import storage


#deployment
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
service = Service(os.environ.get("CHROMEDRIVER_PATH"))
selenium_driver = webdriver.Chrome(service=service,
                                   options=chrome_options)


print(selenium_driver)


#local testing
# selenium_driver = webdriver.Chrome()

logging.basicConfig(level=logging.INFO, format='%(levelname)s:     %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
def health_check():
    #selenium_driver.quit()
    return "OK"

@router.post('/api/trigger')
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
        try:
            new_listing = classifieds.listing_url_to_dictionary(selenium_driver, scraped_url)
            print(new_listing)
            new_listing = {key: new_listing[key] for key in metric_list}
            master_df = pd.concat([master_df, pd.DataFrame(new_listing, index = [0])]).reset_index().drop(columns = ['index'])
        except:
            pass
    master_df = master_df.drop_duplicates(subset = ['id'])
    selected_list = ['tausch','swap','zwischenmiete','wg']
    master_df.loc[(master_df['wohnfläche'] >= 40) &
                    (master_df['wohnfläche'] < 80) &
                    (master_df['miete'] > 500) &
                    (master_df['miete'] < 1300) &
                    (master_df['etage'] >= 3) &
                    (master_df['tauschangebot'] != 'nurtausch') &
                    (master_df['district'].isin(['Prenzlauer Berg','Pankow','Mitte']) == True) &
                    (master_df['url'].str.contains('|'.join(selected_list)) == False), 'is_right_fit'] = 1
    master_df['is_right_fit'] = master_df['is_right_fit'].fillna(0)
    #selenium_driver.quit()
    print(master_df.head(4))
    #right_fit_df = master_df[master_df['is_right_fit'] == 1]
    #master_df.to_parquet(f'gs://kleineinzeigen/test_{str(current_date)}_{str(current_hour)}.parquet')
    return 'Action triggered!'