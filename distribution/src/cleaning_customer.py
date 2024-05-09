# Import libraries
import os
import pandas as pd
from typing import Tuple
from src.params import MASTER_PATH, RAW_DATA_PATH, CLEAN_DATA_PATH, CUSTOMERS

########################################################################################################################

def get_clients() -> pd.DataFrame:
    """
    Retrieves client information from the latest file in the Client Master Files folder.

    Returns:
        pd.DataFrame: DataFrame containing client information.
    """
    # Construct the folder path for the Client Master Files
    folder_path = os.path.join(MASTER_PATH, '01_Client Master Files')

    # Get the latest file path from the folder
    file_path = os.path.join(folder_path, sorted(os.listdir(folder_path), reverse=True)[0])

    # Read the Client Master File into a DataFrame
    clients = pd.read_excel(file_path)

    return clients

########################################################################################################################

def get_titles(customer: str) -> pd.DataFrame:
    """
    Retrieves the report titles from the Report Title Master File.

    Arguments:
        customer (str): The name of the customer.

    Returns:
        pd.DataFrame: DataFrame containing the report titles.
    """
    # Construct folder path for report title master files
    folder_path = os.path.join(MASTER_PATH, '02_Report Title Master Files')

    # Construct file name for customer specific report title master file
    file_name = f'{customer}_Report Title Master File.xlsx'

    # Get the latest file path from the folder
    file_path = os.path.join(folder_path, file_name)

    # Read the latest file into a DataFrame
    titles = pd.read_excel(file_path)

    return titles

########################################################################################################################

def get_firm_name(df: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
    """
    Update the 'Firm Name' column based on matching domains with the 'Domain' column
    of the Client Master file.

    Arguments:
        df (pd.DataFrame):      DataFrame to be updated.
        clients (pd.DataFrame): DataFrame containing domains and their corresponding firm names.

    Returns:
        pd.DataFrame: The updated DataFrame with the 'Firm Name' column modified.
    """
    # Extract the domain from the email address
    df['Domain'] = [email.split('@')[1].split('.')[0] for email in df['Email']]

    # Create a dictionary mapping titles to post dates from the 'titles' dataframe
    firm_name_map = clients.set_index('Domain')['Client'].to_dict()

    # Map the 'Title' column in 'master_data' to the 'Post Date' column in the dictionary
    df['Firm Name'] = df['Domain'].map(firm_name_map)

    # Replace empty values with the default '非公開'
    df['Firm Name'].fillna('非公開', inplace=True)

    return df

########################################################################################################################

def get_client_info(firm_name, clients) -> Tuple[str, str, bool]:
    """
    Gets client information based on firm name from the clients DataFrame.

    Arguments:
        firm_name (str): The name of the firm for which information is to be retrieved.
        clients (DataFrame): DataFrame containing client information.

    Returns:
        Tuple[str, str, bool]: A tuple containing investor type, investor style, and a boolean indicating if the firm is found in the Client Master file.
    """
    # Creating a mask to filter clients DataFrame
    mask = clients['Client'].str.upper() == firm_name.upper()

    # If there's any match
    if mask.any():
        # Extracting necessary information from matching row
        investor_type = clients.loc[mask, 'Investor Type'].iloc[0]
        investor_style = clients.loc[mask, 'Investor Style'].iloc[0]
        is_client = True
        return investor_type, investor_style, is_client
    else:
        # Returning default values if no match found
        return '非公開', '非公開', False

########################################################################################################################

def get_city_and_country(row: pd.Series, clients: pd.DataFrame) -> pd.Series:
    """
    Replaces the values in the 'City' and 'Country' columns of a master_data row
    with values from the corresponding columns in the clients DataFrame if certain conditions are met.

    Arguments:
        row (pandas.Series):        Pandas Series representing a row of a DataFrame, containing 'Firm Name', 'City', and 'Country' columns.
        clients (pandas.DataFrame): DataFrame containing information about clients, with columns 'Client', 'City', and 'Country'.

    Returns:
        pandas.Series: The input row with 'City' and 'Country' values replaced if conditions are met.
    """
    # Finding the client row based on 'Firm Name'
    client_row = clients[clients['Client'] == row['Firm Name']]

    # Proceed if a matching client row was found
    if not client_row.empty:
        # Replacing City values if client exists and has valid city value
        if client_row['City'].iloc[0] != '非公開':
            row['City'] = client_row['City'].iloc[0]

        # Replacing Country values if client exists and has valid country value
        if client_row['Country'].iloc[0] != '非公開':
            row['Country'] = client_row['Country'].iloc[0]

    return row

########################################################################################################################

def add_shortened_title(report_title: str, titles: pd.DataFrame) -> str:
    """
    Find the corresponding, shortened title from the Report Title Master File.

    Arguments:
        report_title (str):        Original title to be shortened
        titles (pandas.DataFrame): DataFrame containing the mappings from original to shortened title.

    Returns:
        str: Shortened title to be added to the 'Title' column.
    """
    # Iterate through titles in the DataFrame
    for title in titles['Title']:
        # Check if the title is part of the report title
        if title.lower() in report_title.lower():
            # Return the shortened title
            return title

    for i, content in enumerate(titles['Content']):
        # Check if the title is part of the report title
        if content.replace(' ', '').lower() in report_title.replace(' ', '').lower():
            # Return the shortened title
            return titles['Title'].iloc[i]

    # If no matching shortened title found, return the original report title
    return report_title

########################################################################################################################

def get_post_date(df: pd.DataFrame, titles: pd.DataFrame) -> pd.DataFrame:
    """
    Update the 'Post Date' column in the input DataFrame based on matching titles
    with the 'Title' column in another DataFrame.

    Arguments:
        df (pd.DataFrame):     DataFrame to be updated.
        titles (pd.DataFrame): DataFrame containing titles and their corresponding post dates.

    Returns:
        pd.DataFrame: The updated DataFrame with the 'Post Date' column modified.
    """
    titles['Post Date'] = pd.to_datetime(titles['Post Date']).dt.date

    # Create a dictionary mapping titles to post dates from the 'titles' dataframe
    post_date_map = titles.set_index('Title')['Post Date'].to_dict()

    # Map the 'Title' column in 'master_data' to the 'Post Date' column in the dictionary
    df['Post Date'] = df['Title'].map(post_date_map)

    return df

########################################################################################################################

def save_missing_clients(df: pd.DataFrame, customer: str) -> None:
    """
    Save clients that are missing in the Client Master DataFrame to a file.

    Arguments:
        df (pandas.DataFrame):  DataFrame to be saved.
        customer (str):         The name of the customer.

    Returns:
        None
    """
    new_df = df[df['In Client Master'] == False]

    if new_df.empty:
        return None

    # Construct output file name, example 'Acant Missing Clients'
    output_file = f'{customer} Missing Clients.xlsx'

    # Construct output file path, example '01_Master Files/01_Client Master Files/01_Missing Clients'
    output_path = os.path.join(MASTER_PATH, '01_Client Master Files', '01_Missing Clients')

    # Check if there are any existing files in the folder
    existing_files = os.listdir(output_path)

    if existing_files and output_file in existing_files:
        # If there are existing files, read the latest one and concatenate it with new_df
        customer_file = os.path.join(output_path, output_file)
        existing_df = pd.read_excel(customer_file)
        concatenated_df = pd.concat([existing_df, new_df]).drop_duplicates()

        # Save constructed file in the output folder
        concatenated_df.to_excel(os.path.join(output_path, output_file), index=False)
    else:
        # If no existing files, directly save new_df to a new file in the output folder
        new_df.to_excel(os.path.join(output_path, output_file), index=False)

    return None

########################################################################################################################

def save_clean_file(df: pd.DataFrame, output_path: str, customer: str, publisher: str) -> None:
    """
    Save cleaned DataFrame to a file.

    Arguments:
        df (pandas.DataFrame):  DataFrame to be saved.
        output_path (str):      Path to the directory where the file will be saved.
        customer (str):         Name of the customer.
        publisher (str):        Name of the publisher.

    Returns:
        None
    """
    # Construct output file name, example: '2024-03-07 Factset Precleaned.xlsx'
    output_file = f'{customer} {publisher} Clean Data.xlsx'

    # Save file in folder '03_Customers/Customer/01_Clean Data'
    df.to_excel(os.path.join(output_path, output_file), index=False)

    return None

########################################################################################################################

def main(publisher, customer):
    # Get clients and titles DataFrame
    clients = get_clients()
    titles = get_titles(customer)

    # Get a customers stock code
    stock_code = str(CUSTOMERS.get(customer))

    # Construct input path for precleaned data
    input_path = os.path.join(RAW_DATA_PATH, '02_Precleaned', publisher)

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
    file_path = os.path.join(input_path, sorted(os.listdir(input_path), reverse=True)[0])

    # Read the latest file into a DataFrame
    master_data = pd.read_excel(file_path)

    # Map the email domain to firm names, where possible
    if publisher in ['Example Publisher 7', 'Example Publisher 8']:
        master_data = get_firm_name(master_data, clients)

    # Process the master data
    master_data = (master_data[master_data['Report Title'].str.contains(stock_code, na=False)]
                   .assign(**{'Investor Type': lambda x: x['Firm Name'].apply(get_client_info, args=(clients,)).str[0],
                              'Investor Style': lambda x: x['Firm Name'].apply(get_client_info, args=(clients,)).str[1],
                              'In Client Master': lambda x: x['Firm Name'].apply(get_client_info, args=(clients,)).str[2]})
                   .apply(get_city_and_country, args=(clients,), axis=1))

    # Add shortened title if there are any rows to process
    if not master_data.empty:
        master_data = master_data.assign(Title=lambda x: x.apply(lambda row: add_shortened_title(row['Report Title'], titles), axis=1))

        # Check and update the Post Date, when necessary
        master_data = get_post_date(master_data, titles).dropna()

    # Identify missing clients and save them
    missing_clients = master_data[master_data['In Client Master'] == False]
    save_missing_clients(missing_clients, customer)

    # Reindex and save the cleaned master data
    master_data = master_data.reindex(columns=[
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

    # Save the cleaned master data
    save_clean_file(master_data, output_path, customer, publisher)

if __name__ == "__main__":
    main()
