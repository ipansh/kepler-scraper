from scrapy import Selector
import requests
import pandas as pd
import datetime

def get_wg_gesucht_listings():
    url = 'https://www.wg-gesucht.de/1-zimmer-wohnungen-und-wohnungen-in-Berlin.8.1+2.1.0.html#back_to_ad_9161625'
    html = requests.get(url).text
    sel = Selector(text = html)
    listings_list = list(sel.xpath('//*[contains(@class,"wgg_card offer_list_item  ")]/div/div/a/@href').extract())
    listings_list = list(set(listings_list))
    return [listing for listing in listings_list if listing.endswith('html')]

def scrape_wg_gesucht_data(input_list):
    """Function for scraping data from each individual listing."""
    appended_data = []
    counter = 0
    for listing in input_list:
        try:
            print(listing)
            #try:
            listing_html = 'https://www.wg-gesucht.de/'+listing
            html = requests.get(listing_html).text
            sel = Selector(text = html)
            apartment_dict = {}
            print('listing...', end = ' ')
            apartment_dict['url'] = listing_html
            #1. listing size
            print('size...', end = ' ')
            apartment_dict['size'] = sel.xpath('//*[contains(@class,"headline headline-key-facts")]/text()').extract()[0].strip() 
            #2. rent
            print('rent...', end = ' ')
            apartment_dict['rent'] = sel.xpath('//*[contains(@class,"headline headline-key-facts")]/text()').extract()[2].strip()   
            #3. rooms
            print('rooms...', end = ' ')
            if len(sel.xpath('//*[contains(@class,"headline headline-key-facts")]/text()').extract()) == 6:
                apartment_dict['rooms'] = sel.xpath('//*[contains(@class,"headline headline-key-facts")]/text()').extract()[4].strip()
            else:
                pass
            #4. floor
            #print('floor...', end = ' ')
            #raw_floor = sel.xpath('//*[contains(@class,"col-xs-6 col-sm-4 text-center print_text_left")]/text()').extract()[2]
            #apartment_dict['floor'] = ''.join(raw_floo r.split())
            #5. deposit
            print('deposit...', end = ' ')
            if sel.xpath('//*[contains(@id,"kaution")]/@value') != []:
                apartment_dict['deposit'] = sel.xpath('//*[contains(@id,"kaution")]/@value').extract()[0]
            else:
                pass
            #6. address_street
            print('street...', end = ' ')
            raw_street = sel.xpath('//*[contains(@class,"col-sm-4 mb10")]/a/text()').extract()[0]
            apartment_dict['street'] = ' '.join(raw_street.split())
            #7. district
            print('location...', end = ' ')
            raw_district = sel.xpath('//*[contains(@class,"col-sm-4 mb10")]/a/text()').extract()[1]
            apartment_dict['location'] = ' '.join(raw_district.split())
            #8. available_from
            print('available from...', end = ' ')
            apartment_dict['available_from'] = sel.xpath('//*[contains(@class,"col-sm-3")]/p/b/text()').extract()[0]
            #9. term
            #available_until
            print('available until...')
            if 'frei bis:' in [item.strip() for item in sel.xpath('//*[contains(@class,"col-sm-3")]/p/text()').extract()]:
                output_term = sel.xpath('//*[contains(@class,"col-sm-3")]/p/b/text()').extract()[1]
            else:
                output_term = 'unlimited'
            apartment_dict['available_until'] = output_term
            #10. tausch
            if 'Tauschangebot' in [item.strip() for item in sel.xpath('//*[contains(@class,"col-sm-3")]/p/text()').extract()]:
                tausch = True
            else:
                tausch = False
            apartment_dict['tausch'] = tausch
            appended_data.append(apartment_dict)
            counter = counter+1
            if counter%10 == 0:
                print('Aggregated listings: {}.'.format(counter), end = ' ')
                #time.sleep(10)
        except:
            listing+' passed!'
            pass
    df = pd.DataFrame(appended_data)
    df = df.reset_index().rename(columns = {'index':'id'})
    return df

def clean_and_filter_gesucht_data(final_df):
    final_df['size'] = [int(size.strip('m²')) for size in final_df['size']]
    final_df['rent'] = [int(rent.strip('€')) for rent in final_df['rent']]
    final_df['district'] = [location.split(' ')[-1] for location in final_df['location']]
    final_df['zipcode'] = [location.split(' ')[0] for location in final_df['location']]
    filtered_df = final_df[(final_df['rent'] < 1500) &
                       (final_df['available_until'] == 'unlimited') &
                       (final_df['tausch'] == False)
                       (final_df['district'].isin(['Pankow','Charlottenburg','Mitte','Berg','Wedding']))]
    filtered_df = filtered_df[['url','size','rent','rooms','deposit','street','district','zipcode','available_from']]
    return filtered_df


def scrape_kleinanzeigen(selenium_driver):
    selenium_driver.get("https://www.kleinanzeigen.de/s-wohnung-mieten/berlin/c203l3331")
    selenium_response = selenium_driver.page_source
    new_selector = Selector(text=selenium_response)
    listings = new_selector.xpath('//*[contains(@class,"text-module-begin")]/a/@href').extract()
    url_list = ['https://www.kleinanzeigen.de'+listing for listing in listings]
    return url_list

def listing_url_to_dictionary(selenium_driver, input_url):
        listing_dict = {}
        try:
                selenium_driver.get(input_url)
                selenium_response = selenium_driver.page_source
                new_selector = Selector(text=selenium_response)
                listing_dict['id'] = input_url.split('/')[-1]
                listing_name = new_selector.xpath('//h1[@id = "viewad-title"]/text()').extract()[0]
                listing_name = listing_name.strip('\n').lstrip(' ')
                listing_dict['name'] = listing_name.lower()

                key_list = [item.strip('\n').replace(' ','')
                        for item in new_selector.xpath('//li[@class = "addetailslist--detail"]/text()').extract()
                        if item.strip('\n').lstrip(' ') != '']

                value_list = [item.strip('\n').replace(' ','')
                        for item in new_selector.xpath('//span[@class = "addetailslist--detail--value"]/text()').extract()
                        if item.strip('\n').lstrip(' ') != '']

                for key, value in zip(key_list, value_list):
                        key = key.lower()
                        value = value.lower()
                        listing_dict[key] = value

                metric_list = list(listing_dict.keys())

                if 'wohnfläche' in metric_list:
                        listing_dict['wohnfläche'] = int(listing_dict['wohnfläche'].rstrip('m²').split(',')[0])
                else:
                        listing_dict['wohnfläche'] = -1

                if 'zimmer' in metric_list:
                        listing_dict['zimmer'] = int(listing_dict['zimmer'].split(',')[0])
                else:
                        listing_dict['zimmer'] = -1

                if 'schlafzimmer' in metric_list:
                        listing_dict['schlafzimmer'] = int(listing_dict['schlafzimmer'].split(',')[0])
                else:
                        listing_dict['schlafzimmer'] = -1

                if 'badezimmer' in metric_list:
                        listing_dict['badezimmer'] = int(listing_dict['badezimmer'].split(',')[0])
                else:
                        listing_dict['badezimmer'] = -1

                if 'warmmiete' in metric_list:
                        listing_dict['warmmiete'] = int(listing_dict['warmmiete'].rstrip(' €').rstrip('€ VB').replace('.',''))
                else:
                        listing_dict['warmmiete'] = -1

                if 'kaution/genoss.-anteile' in metric_list:
                        listing_dict['kaution/genoss.-anteile'] = int(listing_dict['kaution/genoss.-anteile'].rstrip(' €').rstrip('€ VB').replace('.',''))
                else:
                        listing_dict['kaution/genoss.-anteile'] = -1

                if 'etage' in metric_list:
                        listing_dict['etage'] = int(listing_dict['etage'].replace('.',''))
                else:
                        listing_dict['etage'] = -1

                if 'nebenkosten' in metric_list:
                        listing_dict['nebenkosten'] = int(listing_dict['nebenkosten'].rstrip('€').rstrip(' €').rstrip('€ VB').replace('.',''))
                else:
                        listing_dict['nebenkosten'] = -1

                if 'heizkosten' in metric_list:
                        listing_dict['heizkosten'] = int(listing_dict['heizkosten'].rstrip('€').rstrip(' €').rstrip('€ VB').replace('.',''))
                else:
                        listing_dict['heizkosten'] = -1

                listing_dict['scraped_date'] = str(datetime.datetime.now().date())

                for string_metric in ['wohnungstyp','verfügbarab','online-besichtigung','tauschangebot']:
                        if string_metric not in metric_list:
                                listing_dict[string_metric] = 'NA'
                        else:
                                pass

                location = new_selector.xpath('//span[@id = "viewad-locality"]/text()').extract()[0]
                zipcode = location.strip('\n').lstrip(' ').split(' - ')[0]
                zipcode = zipcode.split(' ')[0]
                listing_dict['zipcode'] = zipcode
                district = location.strip('\n').lstrip(' ').split(' - ')[1]
                listing_dict['district'] = district
                price = new_selector.xpath('//h2[@id = "viewad-price"]/text()').extract()[0]
                price = price.lstrip('\n').lstrip(' ').rstrip(' €').rstrip('€ VB').replace('.','')
                listing_dict['miete'] = int(price)
                listing_dict['url'] = input_url
                print('Listing read success!')
        except:
              print('Failure!')
        return listing_dict