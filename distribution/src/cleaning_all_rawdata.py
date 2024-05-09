# Import libraries
import warnings
import os
import pandas as pd
from src.cleaning_rawdata import *
from src.cleaning_customer import *
from src.params import RAW_DATA_PATH, CLEAN_DATA_PATH, PUBLISHERS, CUSTOMERS

warnings.filterwarnings("ignore")

########################################################################################################################

def combine_missing_client_files() -> None:
    """
    Save ca combined copy of all the missing client files.

    Returns:
        None
    """
    # Construct output file name
    output_file = f'All Missing Clients.xlsx'

    # Construct output file path
    path = os.path.join(MASTER_PATH, '01_Client Master Files', '01_Missing Clients')

    # Generate list of file paths, containing each file in the directory
    file_paths = [os.path.join(path, file) for file in os.listdir(path)]

    # If the folder is empty, break function call
    if not file_paths:
        print('Ended')
        return None

    # List containing all loaded files as DataFrames
    dfs = [pd.read_excel(file) for file in file_paths]

    # Generate one combined DataFrame
    df = pd.concat(dfs, ignore_index=True).sort_values(by='Firm Name').reset_index(drop=True)

    # Save file in folder '03_Customers/Customer/01_Clean Data'
    df.to_excel(os.path.join(path, output_file), index=False)

    return None

########################################################################################################################

def main():
    # Get clients DataFrame
    clients = get_clients()

    for publisher in PUBLISHERS:    # Get the number of header and footer rows, as well as column names if publisher is QUICK
        print(f'---------- Now processing: {publisher} ----------')
        header, footer, column_names = get_publisher_info(publisher)

        # Construct input path for uncleaned and precleaned data
        uncleaned_file_path = os.path.join(RAW_DATA_PATH, '01_Uncleaned', publisher)
        precleaned_file_path = os.path.join(RAW_DATA_PATH, '02_Precleaned', publisher)

        # Create publisher folder if it doesn't exist
        if not os.path.exists(precleaned_file_path):
            os.makedirs(precleaned_file_path)

        # Generate list of file paths, containing each file in the directory
        file_paths = [os.path.join(uncleaned_file_path, file) for file in os.listdir(uncleaned_file_path)]

        # Check if the folder is empty
        if not file_paths:
            print("No files found in the folder. Exiting...")
            continue

        # Read the files into a DataFrame
        publisher_data = get_data(header, footer, column_names, file_paths)

        # Process the publisher data
        publisher_data = preclean_data(publisher_data, publisher)

        # Save the precleaned publisher data
        save_precleaned_file(publisher_data, precleaned_file_path, publisher)
        print('\n')

        for i, customer in enumerate(CUSTOMERS, 1):
            print('Customer:', customer)
            print(f'\rCleaning Customers: {i}/{len(CUSTOMERS)} [{i / len(CUSTOMERS) * 100:.2f}%]', end='', flush=True)
            # Get a customers stock code
            stock_code = str(CUSTOMERS.get(customer))

            # Construct input path for precleaned data
            precleaned_file_path = os.path.join(RAW_DATA_PATH, '02_Precleaned', publisher)

            # Construct path for customer folder and its subfolder
            customer_folder = os.path.join(CLEAN_DATA_PATH, customer)

            # Create customer folder and its subfolder if they don't exist
            if not os.path.exists(customer_folder):
                os.makedirs(customer_folder)
            subfolder_path = os.path.join(customer_folder, '01_Clean Data')
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)

            # Set output path to the '01_Clean Data' subfolder
            output_path = os.path.join(customer_folder, '01_Clean Data')

            # Get latest file path from input path
            file_path = os.path.join(precleaned_file_path, sorted(os.listdir(precleaned_file_path), reverse=True)[0])

            # Read the latest file into a DataFrame
            customer_data = pd.read_excel(file_path)

            # Map the email domain to firm names, where possible
            if publisher in ['Example Publisher 7', 'Example Publisher 8']:
                customer_data = get_firm_name(customer_data, clients)

            # Process the customer data
            customer_data = (customer_data[customer_data['Report Title'].str.contains(stock_code, na=False)]
                           .assign(**{'Investor Type': lambda x: x['Firm Name'].apply(get_client_info, args=(clients,)).str[0],
                                      'Investor Style': lambda x: x['Firm Name'].apply(get_client_info, args=(clients,)).str[1],
                                      'In Client Master': lambda x: x['Firm Name'].apply(get_client_info, args=(clients,)).str[2]})
                           .apply(get_city_and_country, args=(clients,), axis=1))

            # Get titles DataFrame
            titles = get_titles(customer)

            if not customer_data.empty:
                # Add shortened title if there are any rows to process
                customer_data = customer_data.assign(Title=lambda x: x.apply(lambda row: add_shortened_title(row['Report Title'], titles), axis=1))

                # Check and update the Post Date, when necessary
                customer_data = get_post_date(customer_data, titles).dropna()

            # Identify missing clients and save them
            missing_clients = customer_data[customer_data['In Client Master'] == False]
            save_missing_clients(missing_clients, customer)

            # Reindex and save the cleaned master data
            customer_data = customer_data.reindex(columns=[
                                                 'Read Date',
                                                 'Firm Name',
                                                 'City',
                                                 'Country',
                                                 'Post Date',
                                                 'Report Title',
                                                 'Title',
                                                 'Platform',
                                                 'Investor Type',
                                                 'Investor Style'
                                             ]).reset_index(drop=True)

            save_clean_file(customer_data, output_path, customer, publisher)
        print('\n')

    combine_missing_client_files()

if __name__ == "__main__":
    main()
