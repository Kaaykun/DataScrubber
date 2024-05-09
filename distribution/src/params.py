# Import libraries
import os
import pandas as pd

#####################  PATH  #####################

ROOT_PATH = os.path.join(os.path.expanduser("~"), "non-disclosed-company.com", "SharepointFolder", "Data")
MASTER_PATH = os.path.join(ROOT_PATH, '01_Master Files')
RAW_DATA_PATH = os.path.join(ROOT_PATH, '02_Raw Data')
CLEAN_DATA_PATH = os.path.join(ROOT_PATH, '03_Customers')

##################  PUBLISHERS  ##################
"""
If a new publisher is added or an existing publisher is no longer used, or
if the file formatting of a publisher changes, please update the Publisher Master File.

Usage: Publisher: Enter the name of the publisher.
       Header:    Enter the number of columns above the column names.
       Footer:    Enter the number of columns with unnecessary info at the bottom of the table.
"""
publishers_df = pd.read_excel(os.path.join(MASTER_PATH, 'Publisher Master File.xlsx'))
PUBLISHERS = publishers_df.set_index('Publisher').to_dict(orient='index')

###################  CUSTOMERS  ###################
"""
If a new customer is added or an existing customer is no longer serviced, or
if the stock code of a customer changes, please update the Customer Stock Code Master File.

Usage: Customer:    Enter the name of the customer.
       Stock Code:  Enter the stock code of the customer.
"""
customers_df = pd.read_excel(os.path.join(MASTER_PATH, 'Customer Stock Code Master File.xlsx'))
CUSTOMERS = dict(zip(customers_df['Customer'], customers_df['Stock Code']))

###################  COUNTRIES  ##################
"""
Different publishers use different country codes. If a country code is not correctly translated into
it's respective country name, add the country code & country name to the Country Mapping Master File.

Usage: Country Code: Country Code that is not translated. 
       Country:      Country Name that should be mapped to the Country Code.
"""
country_df = pd.read_excel(os.path.join(MASTER_PATH, 'Country Mapping Master File.xlsx'))
CUSTOM_COUNTRY_MAPPING = dict(zip(country_df['Country Code'], country_df['Country']))

####################  CITIES  ####################
"""
Sometimes the publishers recorded city name is actually just an area of a bigger city (e.g. Chiyoda-ku).
To transform them into the respective city, add the faulty entries to City Mapping Master File.

Usage: Wrong City:   Incorrect City Name that needs to be updated.
       Correct City: City Name that should be mapped to the Wrong City.
"""
city_df = pd.read_excel(os.path.join(MASTER_PATH, 'City Mapping Master File.xlsx'))
CUSTOM_CITY_MAPPING = dict(zip(city_df['Wrong City'], city_df['Correct City']))
