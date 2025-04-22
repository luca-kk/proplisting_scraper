import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import time
import csv
import math
import random
from datetime import datetime

def clear():
    # Clear the console screen
    os.system('cls' if os.name == 'nt' else 'clear')

def save_df(all_prop, file_name, query):
    # Save the DataFrame to a CSV file

    dir_save = os.getcwd()
    new_dir = os.path.join(dir_save, 'output')
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    os.chdir(new_dir)

    if all_prop == []:
        os.chdir(dir_save)
        with open(f'Warnings.txt', 'a') as file:
            now = datetime.now()
            file.write(f'{file_name} - {now.strftime("%d/%m/%Y %H:%M")}')

    df = pd.DataFrame(all_prop)
    if query == 'sold':
        df['Sold Date'] = pd.to_datetime(df['Sold Date'])
        df = df.sort_values(by='Sold Date', ascending=False)
    df.to_csv(file_name, index=False, encoding='utf-8')
    os.chdir(dir_save)

def get_suburb():
    # Get suburb from user input and return the formatted URL variable

    with open('suburb_data.csv', 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        suburb_data = [row for row in csv_reader]

    while True:
        suburb = input('Enter suburb:  ').title()
        suburb_found = False
        use_url = False
        if suburb.lower() == 'url':
            clear()
            use_url = True
            url_variable = input('Enter URL:  ')
            return url_variable, use_url
        for entry in suburb_data:
            if entry['Suburb'] == suburb:
                url_variable = "-".join(filter(None, ["-".join(suburb.lower().split()), entry["State"].lower(), entry["Zip"]]))
                suburb_found = True
        if suburb_found:
            break
        else:
            clear()
            print('Suburb not found!\n')
            continue

    return url_variable, use_url, suburb.lower()

def options():
    # Get options from user input

    while True:
        try:
            t = int(input('Maximum time pause (3 or above):  '))
            if t < 3:
                raise Exception
            break
        except:
            clear()
            print('Invalid time! Must be at least 3 seconds.\n')
            continue

    while True:
        try:
            ssubs_choice_dict = {1: False, 0: True}
            ssubs_choice = int(input('Surrounding suburbs? (1=yes, 0=no)  '))
            if ssubs_choice not in [0, 1]:
                raise Exception
            ssubs = ssubs_choice_dict[ssubs_choice]
            break
        except:
            clear()
            print('Invalid choice!\n')
            continue

    while True:
        queries_choices = input('Sale = 1, Rent = 2, Sold = 3:  ')
        choices = re.findall(r'1|2|3', queries_choices)
        sale = rent = sold = False
        if '1' in choices:
            sale = True
        if '2' in choices:
            rent = True
        if '3' in choices:
            sold = True
        if sale == rent == sold == False:
            clear()
            print('Must select at least 1 query!\n')
            continue
        break

    if sale == rent == True:
        while True:
            try:
                stats_choice_dict = {1: True, 0: False}
                stats_choice = int(input('Generate stats? (1=yes, 0=no)  '))
                if stats_choice not in [0, 1]:
                    raise Exception
                stats = stats_choice_dict[stats_choice]
                break
            except:
                clear()
                print('Invalid choice!\n')
                continue
    else:
        stats = False

    while True:
        try:
            cp = input('Custom pages:  ')
            if cp.isnumeric():
                if int(cp) < 1:
                    raise Exception
                break
            elif cp == '':
                cp = False
                break
            else:
                raise Exception
        except:
            clear()
            print('Invalid entry!\n')
            continue

    print('Data extraction beginning ...')

    return t, ssubs, stats, sale, rent, sold, cp

def url_to_pages_count(url, query):
    # Get the number of pages from the URL and return it along with a warning if necessary

    warning_dict = {'sale': '1,000', 'rent': '1,000', 'sold' : '2,000'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        summary = soup.find(attrs={'data-testid': 'summary'}).text.strip()
        no_of_prop = int(re.findall(r'\d+(?= Prop)|\d+(?=,)', summary)[0])
        if no_of_prop > 1000:
            pages = 51
            warning = f'\n\nWarning - Over {warning_dict[query]} results ({no_of_prop}) may cause missing data.'
        else:
            pages = math.ceil(no_of_prop/20) + 1
            warning = ''
    except:
        warning = ''
        pages = 1

    return pages, warning

def url_to_listing_soups(url):
    # Get the listings from the URL and return them as BeautifulSoup objects

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    listings = []
    for id in re.findall(r'listing-\d+', response.text):
        listings.append(soup.find(attrs={'data-testid': id}))

    return listings

def format_custom_price(pricing, query, sale_method):
    # Format the custom price based on the pricing string and return it

    if pricing != '-':
        values = re.findall(r'(?:\d(?:,|\.)?)+(?:m|M|k|K)?', pricing)
    else:
        return ''
    
    values = [str(int(float(value.replace('m', '').replace('M', '')) * 1_000_000))
              if 'm' in value.lower() else value for value in values]
    values = [str(int(float(value.replace('k', '').replace('K', '')) * 1_000))
              if 'k' in value.lower() else value for value in values]
    values = [value.replace('.00', '') for value in values]
    values = [value for value in values if len(value) > 2]

    if len(values) > 0:
        if query == 'sale':
            if sale_method == 'Auction':
                return ''
            return f'${values[-1]}'
        else:
            return f'${values[0]}'
    else:
        return ''

def return_total_units(address):
    # Get the total number of units from the address using web scraping

    def update_address_element(address_element, string):
        # Remove the string from the address element and return it

        return address_element.replace(string, '').strip()

    address_element = address.split(r'/', 1)[-1].strip() if len(address.split('/', 1)) > 1 else False

    if address_element:
        street_address = next((match for match in address_element.split(',', 1)), False).strip()
        address_element = update_address_element(address_element, street_address)
        zip = next((match for match in re.findall(r'\d{3,4}+', address_element)), False)
        address_element = update_address_element(address_element, zip)
        state = next((match for match in re.findall(r'ACT|NSW|NT|QLD|SA|TAS|VIC|WA', address_element)), False)
        address_element = update_address_element(address_element, state)
        suburb = next((match for match in re.findall(r'(?:[a-zA-Z] ?)+', address_element)), False)

        if any(not var for var in (street_address, zip, state, suburb)):
            return False

        try:
            url_variable = '-'.join(['-'.join(word for word in street_address.split()), '-'.join(word for word in suburb.split()), state, zip]).lower()
            response = requests.get(f'https://www.domain.com.au/building-profile/{url_variable}', headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            units = re.findall(r'\d+', soup.find(attrs={'data-testid': 'location-profile__data-point'}).text)
            total_units = sum(map(int, units))
        except:
            return False
        
    else:
        return False
    
    return total_units

def parse_listing_data(listing, query):
    # Parse the listing data and return it as a dictionary

    # Link to property
    link = next((match for match in re.findall(r'(?<=href=").+?(?=")', str(listing))), '-')

    # Address
    address_raw = listing.find(attrs={'data-testid': 'address-wrapper'})
    address = address_raw.text.strip().replace('\xa0', ' ') if address_raw else '-'

    # Pricing
    pricing_raw = listing.find(attrs={'data-testid': 'listing-card-price'})
    pricing = pricing_raw.text.strip() if pricing_raw else '-'

    # Sale Method
    if query == 'sale':
        if len(re.findall('Auction', pricing)) > 0:
            sale_method = 'Auction'
        elif len(re.findall('\$|Contact Agent|\d{5,20}', pricing)) > 0:
            sale_method = 'Private Sale' 
        else:
            sale_method = 'Private Sale'
    else:
        sale_method = False

    # Custom Price
    custom_price = format_custom_price(pricing, query, sale_method)

    # Property Info
    info_raw = listing.find(attrs={'data-testid': 'listing-card-features-wrapper'})
    info = info_raw.text.strip() if info_raw else '-'
    info_right_raw = next((match for match in re.findall(r'(?<=Parking).+', info)), info).replace('m²', 'm2')
    info_right = re.sub(r'0([A-Z])', r'\1', info_right_raw)
    size = next((match for match in re.findall(r'(?:\d+(?:,|\.)?)+\w+', info_right)), '')
    type = info_right.replace(size, '').strip() if size != '' else info_right.strip()
    if len(re.findall(r'Vacant|vacant|Land|land', type)) > 0:
        bed = bath = parking = ''
    else:
        bed = next((match for match in re.findall(r'\d+(?= Bed)', info)), '0')
        bath = next((match for match in re.findall(r'\d+(?= Bath)', info)), '0')
        parking = next((match for match in re.findall(r'\d+(?= Parking)', info)), '0')

    # Sold Date
    if query == 'sold':
        sold_date_raw = listing.find(attrs={'data-testid': 'listing-card-tag'})
        sold_date_raw_2 = sold_date_raw.text.strip() if sold_date_raw else '-'
        sold_date = next((match for match in re.findall(r'\d{2} \w{3,5} \d{4}', sold_date_raw_2)), '')
    else:
        sold_date = False

    # Total Units
    if address.find(r'/') > 0:
        total_units = return_total_units(address) if return_total_units(address) else ''
    else:
        total_units = ''

    prop_dict = {
        'sale': {'Link' : link, 'Address' : address, 'Total Units': total_units, 'Property Type' : type, 'Size': size, 'Sale Method' : sale_method,
                 'Pricing Info' : pricing, 'Custom Price' : custom_price, 'Bed' : bed, 'Bath' : bath, 'Parking' : parking},
        'rent': {'Link' : link, 'Address' : address, 'Total Units': total_units, 'Property Type' : type, 'Size': size, 'Rent Price' : custom_price,
                 'Bed' : bed, 'Bath' : bath, 'Parking' : parking},
        'sold': {'Link' : link, 'Address' : address, 'Total Units': total_units, 'Property Type' : type, 'Size': size, 'Sold Price' : custom_price,
                 'Sold Date': sold_date, 'Bed' : bed, 'Bath' : bath, 'Parking' : parking},
        }

    return prop_dict[query]

def get_sale_data(url_variable, t, ssubs, cp):
    # Get sale data from the URL and return it as a list of dictionaries

    all_prop = []
    query = 'sale'
    pages, warning = url_to_pages_count(f'https://www.domain.com.au/sale/{url_variable}/?excludeunderoffer=1{"&ssubs=0" if ssubs else ""}', 'sale')

    if cp:
        pages = int(cp) + 1

    for page in range (1, pages):
        clear()
        print(f'- Sale Properties -\n\nPage {page}/{pages-1} in progress ...{warning}')
        if page > 1:
            time.sleep(random.randint(2,t))
        listings = url_to_listing_soups(f'https://www.domain.com.au/sale/{url_variable}/?excludeunderoffer=1{"&ssubs=0" if ssubs else ""}&page={str(page)}')
        for listing in listings:
            prop = parse_listing_data(listing, query)
            all_prop.append(prop)

    return all_prop

def get_sale_data_url(url_variable, t, ssubs, cp):
    # Get sale data from the URL and return it as a list of dictionaries

    all_prop = []
    query = 'sale'
    pages, warning = url_to_pages_count(f'{url_variable}{"&ssubs=0" if ssubs else ""}', 'sale')

    if cp:
        pages = int(cp) + 1

    for page in range (1, pages):
        clear()
        print(f'- Sale Properties -\n\nPage {page}/{pages-1} in progress ...{warning}')
        if page > 1:
            time.sleep(random.randint(2,t))
        listings = url_to_listing_soups(f'{url_variable}{"&ssubs=0" if ssubs else ""}&page={str(page)}')
        for listing in listings:
            prop = parse_listing_data(listing, query)
            all_prop.append(prop)

    return all_prop

def get_rent_data(url_variable, t, ssubs, cp):
    # Get rent data from the URL and return it as a list of dictionaries

    all_prop = []
    query = 'rent'
    pages, warning = url_to_pages_count(f'https://www.domain.com.au/rent/{url_variable}/?excludedeposittaken=1{"&ssubs=0" if ssubs else ""}', 'rent')

    if cp:
        pages = int(cp) + 1

    for page in range (1, pages):
        clear()
        print(f'- Rent Properties -\n\nPage {page}/{pages-1} in progress ...{warning}')
        if page > 1:
            time.sleep(random.randint(2,t))
        listings = url_to_listing_soups(f'https://www.domain.com.au/rent/{url_variable}/?excludedeposittaken=1{"&ssubs=0" if ssubs else ""}&page={str(page)}')
        for listing in listings:
            prop = parse_listing_data(listing, query)
            all_prop.append(prop)

    return all_prop

def get_rent_data_url(url_variable, t, ssubs, cp):
    # Get rent data from the URL and return it as a list of dictionaries

    all_prop = []
    query = 'rent'
    pages, warning = url_to_pages_count(f'{url_variable}{"&ssubs=0" if ssubs else ""}', 'rent')

    if cp:
        pages = int(cp) + 1

    for page in range (1, pages):
        clear()
        print(f'- Rent Properties -\n\nPage {page}/{pages-1} in progress ...{warning}')
        if page > 1:
            time.sleep(random.randint(2,t))
        listings = url_to_listing_soups(f'{url_variable}{"&ssubs=0" if ssubs else ""}&page={str(page)}')
        for listing in listings:
            prop = parse_listing_data(listing, query)
            all_prop.append(prop)

    return all_prop

def get_sold_data(url_variable, t, ssubs, cp):
    # Get sold data from the URL and return it as a list of dictionaries

    # Generating price ranges for URLs
    start = 0  
    end = 50000000
    initial_step = 250000
    large_step = 5000000
    threshold = 5000000
    price_ranges = []
    current = start
    step = initial_step
    while current < end:
        next_range = [current, current + step]
        price_ranges.append(next_range)
        current_temp = current
        current += step
        if current_temp + step >= threshold:
            step = large_step

    all_prop = []
    query = 'sold'

    for pr in price_ranges:
        pages, warning = url_to_pages_count(f'https://www.domain.com.au/sold-listings/{url_variable}/?price={pr[0]}-{pr[1]}&excludepricewithheld=1{"&ssubs=0" if ssubs else ""}', 'sold')
        if warning != '':
            urls = [f'https://www.domain.com.au/sold-listings/{url_variable}/?price={pr[0]}-{pr[1]}&excludepricewithheld=1{"&ssubs=0" if ssubs else ""}&sort=solddate-asc',
                    f'https://www.domain.com.au/sold-listings/{url_variable}/?price={pr[0]}-{pr[1]}&excludepricewithheld=1{"&ssubs=0" if ssubs else ""}&sort=solddate-desc']
        else:
            urls = [f'https://www.domain.com.au/sold-listings/{url_variable}/?price={pr[0]}-{pr[1]}&excludepricewithheld=1{"&ssubs=0" if ssubs else ""}&sort=solddate-asc']

        if cp:
            pages = int(cp) + 1

        pg = 0
        for url in urls:
            for page in range (1, pages):
                clear()
                print(f'- Sold Properties -\n\n${pr[0]} - ${pr[1]}\nPage {pg}/{(pages-1)*len(urls)} in progress ...{warning}')
                if page > 1:
                    time.sleep(random.randint(2,t))
                pg += 1
                listings = url_to_listing_soups(url + '&page=' + str(page))
                for listing in listings:
                    prop = parse_listing_data(listing, query)
                    all_prop.append(prop)

    # De-duplicating
    all_prop_deduped = {}
    all_prop_dupes = {}

    for prop in all_prop:
        link = prop['Link']
        key = link
        if key not in all_prop_deduped:
            all_prop_deduped[key] = prop
        else:
            all_prop_dupes[key] = prop

    all_prop_deduped = list(all_prop_deduped.values())
    all_prop_dupes = list(all_prop_dupes.values())

    # save_df(all_prop_dupes, 'sold_output_dupes.csv', query)

    return all_prop_deduped

def generate_stats(rent_data, sale_data):
    # Generate statistics for the rent and sale data

    def average_rent_prices_2(d):
        if isinstance(d, dict):
            all_values = []

            for key, value in d.items():
                result = average_rent_prices_2(value)
                d[key] = result

                if isinstance(result, (int, float)):
                    all_values.append(result)
                elif isinstance(result, dict) and 'Avg' in result:
                    all_values.append(result['Avg'])

            if all_values:
                d['Avg'] = round(sum(all_values) / len(all_values), 2)

            return d

        elif isinstance(d, list):
            try:
                d = [item for item in d if item != '']
                avg_rent = sum(float(price.replace('$', '').replace(',', '')) for price in d) / len(d)
                return round(avg_rent, 2)
            except Exception as e:
                print(e)
                input(d)
                return 1
        return d

    # warning for shitty data - e.g. if there isnt much data/any data
    # outliers

    clear()
    print('Generating statistics...')

    avg_dict = {}
    for prop in rent_data:
        avg_dict.setdefault(prop['Property Type'], {})\
        .setdefault(prop['Bed'], {})\
        .setdefault(prop['Bath'], {})\
        .setdefault(prop['Parking'], []).append(prop['Rent Price'].replace('$', '').replace(',', ''))

    average_rent_prices_2(avg_dict)

    for prop in sale_data:
        if prop['Sale Method'] == 'Auction' or prop['Custom Price'] == '':
            prop['Est. Yield'] = ''
        else:
            try:
                prop['Est. Rent'] = f"${str(avg_dict[prop['Property Type']][prop['Bed']][prop['Bath']][prop['Parking']])}"
                prop['Est. Yield'] = f"{str(((avg_dict[prop['Property Type']][prop['Bed']][prop['Bath']][prop['Parking']] * 52) / float(prop['Custom Price'].replace('$', '').replace(',', '')) if prop['Custom Price'] != '' else 1) * 100)}%"
                prop['Rent/Yield Meta Used'] = 'Exact'
            except KeyError:
                try:
                    prop['Est. Rent'] = f"${str(avg_dict[prop['Property Type']][prop['Bed']][prop['Bath']]['Avg'])}"
                    prop['Est. Yield'] = f"{str(((avg_dict[prop['Property Type']][prop['Bed']][prop['Bath']]['Avg'] * 52) / float(prop['Custom Price'].replace('$', '').replace(',', '')) if prop['Custom Price'] != '' else 1) * 100)}%"
                    prop['Rent/Yield Meta Used'] = 'Bath Avg.'
                except KeyError:
                    try:
                        prop['Est. Rent'] = f"${str(avg_dict[prop['Property Type']][prop['Bed']]['Avg'])}"
                        prop['Est. Yield'] = f"{str(((avg_dict[prop['Property Type']][prop['Bed']]['Avg'] * 52) / float(prop['Custom Price'].replace('$', '').replace(',', '')) if prop['Custom Price'] != '' else 1) * 100)}%"
                        prop['Rent/Yield Meta Used'] = 'Bed Avg.'
                    except KeyError:
                        try:
                            prop['Est. Rent'] = f"${str(avg_dict[prop['Property Type']]['Avg'])}"
                            prop['Est. Yield'] = f"{str(((avg_dict[prop['Property Type']]['Avg'] * 52) / float(prop['Custom Price'].replace('$', '').replace(',', '')) if prop['Custom Price'] != '' else 1) * 100)}%"
                            prop['Rent/Yield Meta Used'] = 'Prop Type Avg.'
                        except KeyError:
                            prop['Est. Yield'] = ''

if __name__ == '__main__':
    try:
        clear()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, likeecko) Chrome/127.0.0.0 Safari/537.36'}
        url_variable, use_url, suburb = get_suburb()
        t, ssubs, stats, sale, rent, sold, cp = options()

        if use_url:
            if sale:
                sale_data = get_sale_data_url(url_variable, t, ssubs, cp)
            elif rent:
                rent_data = get_rent_data_url(url_variable, t, ssubs, cp)
            else:
                sold_data = []
        else:
            if sale:
                sale_data = get_sale_data(url_variable, t, ssubs, cp)
            if rent:
                rent_data = get_rent_data(url_variable, t, ssubs, cp)
            if sold:
                sold_data = get_sold_data(url_variable, t, ssubs, cp)

        if stats:
            generate_stats(rent_data, sale_data)

        if sale:
            save_df(sale_data, f'sale_output_{suburb}.csv', 'sale')
        if rent:
            save_df(rent_data, f'rent_output_{suburb}.csv', 'rent')
        if sold:
            save_df(sold_data, f'sold_output_{suburb}.csv', 'sold')

        clear()
        print('Extractions complete.')
    except Exception as e:
        clear()
        print(f'An unexpected error occurred: {e}')
        input( 'Press Enter to exit ...')