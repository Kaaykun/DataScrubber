# Import libraries
import os
import re
import datetime
import pycountry
import numpy as np
import pandas as pd
from urllib.parse import unquote
from dateutil import parser
from chardet import detect
from typing import Tuple, List, Union
from src.params import RAW_DATA_PATH, PUBLISHERS, CUSTOM_COUNTRY_MAPPING, CUSTOM_CITY_MAPPING

########################################################################################################################

def get_publisher_info(publisher: str) -> Tuple[int, int, Union[List[str], None]]:
    """
    Get publisher specific formatting information.

    Arguments:
    publisher (str): Name of the publisher.

    Returns:
        header (int):        The number of header rows to remove from the file.
        footer (int):        The number of footer rows to remove from the file.
        column_names (list): Custom column names to insert at the top of the file later.
    """
    # Retrieve header and footer information from the PUBLISHERS dictionary based on the given publisher
    header = PUBLISHERS[publisher]['Header']  # Header information specific to the publisher
    footer = PUBLISHERS[publisher]['Footer']  # Footer information specific to the publisher

    # Determine column names based on the publisher type
    if publisher == 'example_publisher_4':
        # For 'QUICK' publisher, specify column names explicitly
        column_names = ['Read Date', '0', 'Firm Name', '1', '2', 'Post Date', 'Report Title', '3', '4']
    else:
        # For other publishers, set column names to None
        column_names = None

    # Return header, footer, and column names
    return header, footer, column_names

########################################################################################################################

def get_data(header: int, footer: int, column_names: Union[list, None], file_paths: list) -> pd.DataFrame:
    """
    Load data from files into a pandas DataFrame.

    Arguments:
        header (int):        Number of rows to skip from the top.
        footer (int):        Number of rows to skip from the bottom.
        column_names (list): Custom column names to insert at the top.
        file_paths (list):   List of file paths to be loaded.

    Returns:
        pandas.DataFrame: A concatenated DataFrame containing data from all files.
    """
    total_files = len(file_paths)  # Total number of files to load
    dfs = []  # List to store loaded DataFrames

    # Iterate over all files in the publisher-specific '02_Raw Data' folder
    for i, file_path in enumerate(file_paths, 1):
        # Print loading progress
        print(f'\rLoading: {i}/{total_files} [{i / total_files * 100:.2f}%]', end='', flush=True)

        # Determine how to handle files based on column_names availability
        if column_names is not None:
            # Handle files without column names by adding custom column names
            if file_path.upper().endswith('.XLS'):
                df = pd.read_excel(file_path, skiprows=header, skipfooter=footer, names=column_names)
            elif file_path.upper().endswith('.CSV'):
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    encoding = detect(raw_data)['encoding']
                df = pd.read_csv(file_path, skiprows=header, skipfooter=footer, names=column_names, encoding=encoding, encoding_errors='ignore')
            else:
                continue  # Skip unsupported file formats
        else:
            # Handle files with existing column names
            if file_path.upper().endswith('.XLS'):
                df = pd.read_excel(file_path, skiprows=header, skipfooter=footer)
            elif file_path.upper().endswith('.CSV'):
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    encoding = detect(raw_data)['encoding']
                df = pd.read_csv(file_path, skiprows=header, skipfooter=footer, encoding=encoding, encoding_errors='ignore')
            else:
                continue  # Skip unsupported file formats

        # Append loaded DataFrame to the list
        dfs.append(df.astype(str))

    # Concatenate all DataFrames and return the result
    return pd.concat(dfs, ignore_index=True)

########################################################################################################################
def process_columns(df: pd.DataFrame, remove_duplicates: bool = True) -> pd.DataFrame:
    """
    Process columns of a DataFrame.

    Arguments:
        df (pandas.DataFrame):    DataFrame to process.
        remove_duplicates (bool): Whether to remove duplicate rows based on 'Transaction ID'. Defaults to True.

    Returns:
        pandas.DataFrame: Processed DataFrame.
    """
    column_order = [
        'Read Date',
        'Post Date',
        'Firm Name',
        'User Name',
        'Email',
        'City',
        'Country',
        'Report Title',
        'Platform',
        'Transaction ID'
        ]

    # Reorder columns for consistency
    df = df.reindex(columns=column_order)

    # Sort rows by read date
    df = df.sort_values(by='Read Date', ascending=False)

    # Remove duplicate entries from the table
    if remove_duplicates == True:
        df.drop_duplicates(subset='Transaction ID', inplace=True)

    # Reset index for correct row numbering
    df.reset_index(drop=True, inplace=True)

    # Fill all missing or undisclosed information with '非公開' for consistency
    df.replace(['***', 'N/A - Free Content', 'Restricted', 'nan', 'Unattributed', 'Embargoed', 'EMBARGOED', 'Unknown'], '非公開', inplace=True)

    return df

########################################################################################################################

def map_and_fillna_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map country codes to country names and fill missing values in the 'Country' column.

    Arguments:
        df (pandas.DataFrame): DataFrame containing the 'Country' column with country codes.

    Returns:
        pandas.DataFrame: DataFrame with country codes mapped to country names and missing values filled.
    """
    def custom_mapping(country_code):
        if country_code == "非公開":
            return "非公開"

        # Map standard country code to their country names
        try:
            country_name = pycountry.countries.get(alpha_2=country_code).name
        except AttributeError:
            country_name = country_code

        # Apply custom mapping for non standard country codes
        country_name = CUSTOM_COUNTRY_MAPPING.get(country_name, country_name)

        return country_name

    # Map country codes to country names and fill missing values
    df['Country'] = df['Country'].apply(custom_mapping)
    # Transform country names to uppercase
    df['Country'] = df['Country'].apply(lambda x: x.upper() if x != '非公開' else x)

    return df

########################################################################################################################

def map_and_fillna_city(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map city names and fill missing values in the 'City' column.

    Arguments:
        df (pandas.DataFrame): DataFrame containing the 'City' column with city names.

    Returns:
        pandas.DataFrame: DataFrame with city names mapped and missing values filled.
    """
    # Map city names to match existing cities and fill missing values
    df['City'] = df['City'].map(CUSTOM_CITY_MAPPING).fillna(df['City'])
    # Transform city names to uppercase
    df['City'] = df['City'].apply(lambda x: x.upper() if x != '非公開' else x)

    return df

########################################################################################################################

def month_name_to_month(month_name: str) -> str:
    """
    Parse the month name to a date object and extract the month number

    Arguments:
        month_name (str): String containing name of the month.

    Returns:
        int: Month number corresponding to input month name (e.g. January -> 1)
    """
    month = parser.parse(month_name).month

    return month

########################################################################################################################

def save_precleaned_file(df: pd.DataFrame, raw_data_precleaned_path: str, publisher: str) -> None:
    """
    Save pre-cleaned DataFrame to a file.

    Arguments:
        df (pandas.DataFrame):          DataFrame to be saved.
        raw_data_precleaned_path (str): Path to the directory where the file will be saved.
        publisher (str):                Name of the publisher.

    Returns:
        None
    """
    # Get todays Date
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    # Construct filename, example: '2024-03-07 Factset Precleaned.xls'
    output_file = f'{current_date} {publisher} Precleaned.xlsx'
    # Save file in folder '02_Raw Data/02_Precleaned/Publisher'
    df.to_excel(os.path.join(raw_data_precleaned_path, output_file), index=False)

    return None

########################################################################################################################

def clean_example_publisher_1(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process a DataFrame containing example_publisher_1 data.

    Arguments:
        df (pandas.DataFrame): DataFrame containing example_publisher_1 data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """
    # Define columns to keep in the DataFrame
    col_to_keep = [
        'Transaction Date',
        'Customer Name',
        'User Name',
        'Business eMail',
        'Customer City',
        'Customer Country',
        'Transaction Id',
        'Post Date',
        'Title'
        ]

    # Keep only selected columns
    df = df[col_to_keep]

    # Add the Platform column to the DataFrame
    df = df.assign(**{
        'Platform': 'example_publisher_1'
        })

    # Rename columns for clarity and consistency
    df = df.rename(columns={
        'Transaction Date': 'Read Date',
        'Platform':         'Platform',
        'Customer Name':    'Firm Name',
        'User Name':        'User Name',
        'Business eMail':   'Email',
        'Customer City':    'City',
        'Customer Country': 'Country',
        'Transaction Id':   'Transaction ID',
        'Post Date':        'Post Date',
        'Title':            'Report Title'
        })

    # Filter out all non-disclosed company downloads and reset index to maintain continuous index values
    df = df[~df['Firm Name'].str.lower().str.contains('non-disclosed company name')].reset_index(drop=True)

    def convert_date_example_publisher_1(date_str):
        # Format: YYYY/MM/DD HH:MM or DD/MM/YYYY HH:MM
        date, _ = date_str.split(' ')
        if date[2] == '/':
            date = f'{date[6:]}/{date[3:5]}/{date[0:2]}'
        return f"{date.replace('/', '-')}"

    df[['Read Date', 'Post Date']] = df[['Read Date', 'Post Date']].applymap(convert_date_example_publisher_1)

    # Process DataFrame
    df = map_and_fillna_city(map_and_fillna_country(process_columns(df)))

    return df

########################################################################################################################

def clean_example_publisher_2(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process a DataFrame containing example_publisher_2 data.

    Arguments:
        df (pandas.DataFrame): DataFrame containing example_publisher_2 data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """
    # Define columns to keep in the DataFrame
    col_to_keep = [
        'Date/time read',
        'Platform',
        'Parent Firm name',
        'Reader name',
        'E-mail',
        'City',
        'Country',
        'Readership Event ID',
        'Date/time published',
        'Report title'
        ]

    # Keep only selected columns
    df = df[col_to_keep]

    # Rename columns for clarity and consistency
    df = df.rename(columns={
        'Date/time read':                   'Read Date',
        'Platform':                         'Platform',
        'Parent Firm name':                 'Firm Name',
        'Reader name':                      'User Name',
        'E-mail':                           'Email',
        'City':                             'City',
        'Country':                          'Country',
        'Readership Event ID (FactSet)':    'Transaction ID',
        'Date/time published':              'Post Date',
        'Report title':                     'Report Title'
        })

    # Filter out all non-disclosed company downloads and reset index to maintain continuous index values
    df = df[~df['Firm Name'].str.lower().str.contains('non-disclosed company name')].reset_index(drop=True)

    def convert_date_example_publisher_2(date_str):
        # Format: DD-Month-YYYY HH:MM AM/PM
        date, _, _ = date_str.split(' ')
        day, month_name, year = date.split('-')
        month = month_name_to_month(month_name)
        return f"{year}-{month:02d}-{int(day):02d}"

    df[['Read Date', 'Post Date']] = df[['Read Date', 'Post Date']].applymap(convert_date_example_publisher_2)

    # Process DataFrame
    df = map_and_fillna_city(map_and_fillna_country(process_columns(df)))

    return df

########################################################################################################################

def clean_example_publisher_3(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process a DataFrame containing example_publisher_3 data.

    Arguments:
        df (pandas.DataFrame): DataFrame containing example_publisher_3 data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """
    # Define columns to keep in the DataFrame
    col_to_keep = [
        'Viewed Date',
        'Published Date',
        'Client Name',
        'User Name',
        'User Email',
        'User City',
        'User Country',
        'Headline',
        'Transaction ID'
        ]

    # Keep only selected columns
    df = df[col_to_keep]

    # Add the Platform column to the DataFrame
    df = df.assign(**{
        'Platform': 'example_publisher_3'
        })

    # Rename columns for clarity and consistency
    df = df.rename(columns={
        'Viewed Date':      'Read Date',
        'Platform':         'Platform',
        'Client Name':      'Firm Name',
        'User Name':        'User Name',
        'User Email':       'Email',
        'User City':        'City',
        'User Country':     'Country',
        'Transaction ID':   'Transaction ID',
        'Published Date':   'Post Date',
        'Headline':         'Report Title'
        })

    # Filter out all non-disclosed company downloads and reset index to maintain continuous index values
    df = df[~df['Firm Name'].str.lower().str.contains('non-disclosed company name')].reset_index(drop=True)

    def convert_date_example_publisher_3(date_str):
        # Format: MM/DD/YYYY HH:MM:SS
        date, _ = date_str.split(' ')
        month, day, year = date.split('/')
        return f"{year}-{int(month):02d}-{int(day):02d}"

    df[['Read Date', 'Post Date']] = df[['Read Date', 'Post Date']].applymap(convert_date_example_publisher_3)

    # Process DataFrame
    df = map_and_fillna_city(map_and_fillna_country(process_columns(df)))

    return df

########################################################################################################################

def clean_example_publisher_4(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process a DataFrame containing example_publisher_4 data.

    Arguments:
        df (pandas.DataFrame): DataFrame containing example_publisher_4 data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """
    # Define columns to keep in the DataFrame
    col_to_keep = [
        'Read Date',
        'Firm Name',
        'Post Date',
        'Report Title'
        ]

    # Keep only selected columns
    df = df[col_to_keep]

    # Add the Platform, User Name, Email, City, Country and Transaction ID columns to the DataFrame
    df = df.assign(**{
        'Platform':       'example_publisher_4',
        'User Name':      '非公開',
        'Email':          '非公開',
        'City':           '非公開',
        'Country':        '非公開',
        'Transaction ID': '非公開'
        })

    # Filter out all non-disclosed company downloads and reset index to maintain continuous index values
    df = df[~df['Firm Name'].str.lower().str.contains('non-disclosed company name')].reset_index(drop=True)

    def convert_date_example_publisher_4(date_str):
        # Format: YYYY/MM/DD
        return date_str.replace('/', '-')

    df[['Read Date', 'Post Date']] = df[['Read Date', 'Post Date']].applymap(convert_date_example_publisher_4)

    # Process DataFrame
    df = map_and_fillna_city(map_and_fillna_country(process_columns(df, remove_duplicates=False)))

    return df

########################################################################################################################

def clean_example_publisher_5(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process a DataFrame containing example_publisher_5 data.

    Arguments:
        df (pandas.DataFrame): DataFrame containing example_publisher_5 data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """
    # Define columns to keep in the DataFrame
    col_to_keep = [
        'Activity Date',
        'Client Name',
        'Activity Id',
        'Document Posted Date',
        'Headline'
        ]

    # Keep only selected columns
    df = df[col_to_keep]

    # Add the Platform, User Name, Email, City and Country columns to the DataFrame
    df = df.assign(**{
        'Platform':  'example_publisher_5',
        'User Name': '非公開',
        'Email':     '非公開',
        'City':      '非公開',
        'Country':   '非公開'
        })

    # Rename columns for clarity and consistency
    df = df.rename(columns={
        'Activity Date':        'Read Date',
        'Platform':             'Platform',
        'Client Name':          'Firm Name',
        'User Name':            'User Name',
        'Email':                'Email',
        'City':                 'City',
        'Country':              'Country',
        'Activity Id':          'Transaction ID',
        'Document Posted Date': 'Post Date',
        'Headline':             'Report Title'
        })

    # Filter out all non-disclosed company downloads and reset index to maintain continuous index values
    df = df[~df['Firm Name'].str.lower().str.contains('non-disclosed company name')].reset_index(drop=True)

    def convert_date_example_publisher_5(date_str):
        # Format: MM/DD/YYYY HH:MM:SS AM/PM
        date, _, _ = date_str.split(' ')
        month, day, year = date.split('/')
        return f"{year}-{int(month):02d}-{int(day):02d}"

    df['Read Date'] = df['Read Date'].apply(convert_date_example_publisher_5)

    # Process DataFrame
    df = map_and_fillna_city(map_and_fillna_country(process_columns(df)))

    return df

########################################################################################################################

def clean_example_publisher_6(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process a DataFrame containing example_publisher_6 data.

    Arguments:
        df (pandas.DataFrame): DataFrame containing example_publisher_6 data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """
    # Define columns to keep in the DataFrame
    col_to_keep = [
    'Published',
    'Title'
    ]

    # Repeat each row based on the value in the 'Platform Views*' column
    df = df.loc[df.index.repeat(df['Platform Views*'])]
    # Reset index to maintain continuous index values
    df.reset_index(drop=True, inplace=True)

    # Keep only selected columns
    df = df[col_to_keep]

    # Add the Read Date, Platform, Firm Name, User Name, Email, City, Country and Transaction ID columns to the DataFrame
    df = df.assign(**{
        'Read Date':      df['Published'],
        'Platform':       'example_publisher_6',
        'Firm Name':      '非公開',
        'User Name':      '非公開',
        'Email':          '非公開',
        'City':           '非公開',
        'Country':        '非公開',
        'Transaction ID': '非公開'
        })

    # Rename columns for clarity and consistency
    df = df.rename(columns={
        'Read Date':      'Read Date',
        'Platform':       'Platform',
        'Firm Name':      'Firm Name',
        'User Name':      'User Name',
        'Email':          'Email',
        'City':           'City',
        'Country':        'Country',
        'Transaction ID': 'Transaction ID',
        'Published':      'Post Date',
        'Title':          'Report Title'
        })

    # Filter out all non-disclosed company downloads and reset index to maintain continuous index values
    df = df[~df['Firm Name'].str.lower().str.contains('non-disclosed company name')].reset_index(drop=True)

    def convert_date_example_publisher_6(date_str):
        # Format: Month DD, YYYY
        month_name_day, year = date_str.split(', ')
        month_name, day = month_name_day.split(' ')
        month = month_name_to_month(month_name)
        return f"{year}-{int(month):02d}-{int(day.strip()):02d}"

    df[['Read Date', 'Post Date']] = df[['Read Date', 'Post Date']].applymap(convert_date_example_publisher_6)

    # Process DataFrame
    df = map_and_fillna_city(map_and_fillna_country(process_columns(df, remove_duplicates=False)))

    return df

########################################################################################################################

def clean_example_publisher_7(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process a DataFrame containing example_publisher_7 data.

    Arguments:
        df (pandas.DataFrame): DataFrame containing example_publisher_7 data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """
    def pre_cleaning_example_publisher_7(df: pd.DataFrame) -> pd.DataFrame:
        # Custom publishers dictionary used to clean Downloaded Report column
        custom_publishers = {
            'Publisher 1':   '(0001)',
            'パブリシャー 1': '(0001)',
            'Publisher 2':   '(0002)',
            'パブリシャー 2': '(0002)',
            'Publisher 3':   '(0003)',
            'パブリシャー 3': '(0003)',
            'Publisher 4':   '(0004)',
            'パブリシャー 4': '(0004)',
            'Publisher 5':   '(0005)',
            'パブリシャー 5': '(0005)'
        }

        # Custom reports dictionary used to clean Downloaded Report column
        custom_reports = {
            'Initiating coverage':                         '(0001) Initiating coverage',
            'Initiating coverage':                         '(0002) Initiating coverage',
            'Financial model':                             '(0001) Financial model',
            'Transforming for a major sector turnaround':  '(0001) Initiating coverage',
            'Group investments':                           '(0001) Group investments',
            'Q2 FY3/2023 results update':                  '(0001) Q2 FY3/2023 results update',
            'Q3 FY3/2023 results update':                  '(0001) Q3 FY3/2023 results update',
            'Q4 FY3/2023 results update/deep-dive update': '(0001) Q4 FY3/2023 results update/deep-dive update',
            'Q1 FY3/2024 results update':                  '(0001) Q1 FY3/2024 results update',
            'Q2 FY3/2024 results update':                  '(0001) Q2 FY3/2024 results update',
            'Q3 FY3/2022 results update':                  '(0001) Q3 FY3/2022 results update',
            'Q4 FY3/2024 results update/deep-dive update': '(0001) Q4 FY3/2023 results update/deep-dive update',
            'カバレッジ開始':                               '(0001) カバレッジ開始',
            'ニュースリリース(1)':                          '(0001) ニュースリリース（1）',
            'ニュースリリースアラート':                      '(0001) ニュースリリース（1）',
            'ニュースリリースアラート(2)':                   '(0001) ニュースリリース（2）',
            '業績予測モデル':                               '(0001) 業績予測モデル',
            '22年3月期4Q 決算':                            '(0001) 22年3月期4Q 決算',
            '23年3月期1Q 決算':                            '(0001) 23年3月期1Q 決算',
            '23年3月期2Q 決算':                            '(0001) 23年3月期2Q 決算',
            '23年3月期2Q 決算アップデート':                 '(0001) 23年3月期2Q 決算',
            '23年3月期3Q 決算':                            '(0001) 23年3月期3Q 決算',
            '24年3月期3Q 決算':                            '(0001) 24年3月期3Q 決算',
            '24年3月期1Q 決算':                            '(0001) 24年3月期1Q 決算',
            '24年3月期2Q 決算':                            '(0001) 24年3月期2Q 決算',
            '(0003)(サマリー版2)2022.05.13':               '(0003) FY3/2022 results update',
            '(0004)(サマリー版)2022.08.02':                '(0004) Q1 FY3/2024 results update'
        }

        def transform_report_title(url: str) -> str:
            # Replace percent-encoded characters
            stock_code, report_title = unquote(url).translate(str.maketrans('（）', '()')).replace('\u3000', '').split('?document=')

            if stock_code[-4:].isdigit():
                # Rearrange simple strings and return cleaned report title
                return f'({stock_code[-4:]}) ' + report_title.replace('%20', ' ')

            def move_stock_code(report_title: str) -> str:
                # Find substrings enclosed within brackets
                match = re.search(r'\((\d{4})\)', report_title)

                if match:
                    # Extract the substring within brackets
                    bracketed_text = match.group(0)

                    # Remove the substring within brackets from the original string
                    cleaned_report_title = report_title.replace(bracketed_text, '')

                    # Move the substring within brackets to the beginning of the cleaned string
                    return f'{bracketed_text} {cleaned_report_title.strip()}'

                else:
                    return report_title

            # Apply regex search to complicated string and return cleaned report title
            return move_stock_code(report_title.replace('%20', ' '))

        # Replace publishers with corresponding stock codes in the downloaded report title
        def transform_publishers(downloaded_report: str, custom_publishers: dict) -> str:
            for publisher, stock_code in custom_publishers.items():
                if publisher in downloaded_report and not downloaded_report.startswith('('):
                    downloaded_report = downloaded_report.replace(publisher, stock_code)

            return downloaded_report

        def transform_reports(df: pd.DataFrame, custom_reports: dict) -> pd.DataFrame:
            # Sort custom_reports by key length in descending order
            custom_reports = dict(sorted(custom_reports.items(), key=lambda x: len(x[0]), reverse=True))

            # Iterate over each row in the DataFrame
            for index, row in df.iterrows():
                # Loop over each key-value pair in the custom_reports dictionary
                for key, value in custom_reports.items():
                    # If the key is found in the 'Downloaded Report' column and the report doesn't start with '(', replace it with the corresponding value
                    if key in row['Downloaded Report'] and not row['Downloaded Report'].startswith('('):
                        df.at[index, 'Downloaded Report'] = row['Downloaded Report'].replace(key, value)

            return df

        # Apply transformations
        df['Downloaded Report'] = df['Conversion Page'].apply(transform_report_title)
        df['Downloaded Report'] = df['Downloaded Report'].apply(lambda x: transform_publishers(x, custom_publishers))

        # Initialize empty dataframe
        temp_df = pd.DataFrame(columns=df.columns)

        # List to store the indices of rows to be removed
        rows_to_remove = []

        for i, row in df.iterrows():
            # Iterate over rows to filter and move to temp_df
            if not row['Downloaded Report'].startswith('('):
                temp_df = pd.concat([temp_df, pd.DataFrame(row).T])
                rows_to_remove.append(i)

        # Remove rows from df
        df = df.drop(index=rows_to_remove)

        # Apply transformations to temp_df
        temp_df = transform_reports(temp_df, custom_reports)

        # Concatenate temp_df back to df
        df = pd.concat([df, temp_df], ignore_index=True)

        # Replace faulty titles with usable ones
        df['Downloaded Report'] = df['Downloaded Report'].str.replace(r'\(\d+ページ\)|\(\d+ pages\)', '', regex=True)\
                                                             .replace(r'\(0005\)\(サマリー版\).*', '(0005) FY3/2022 results update', regex=True)\
                                                             .replace(r'\(0005\)\(サマリー版2\).*', '(0005) FY3/2022 results update', regex=True)\
                                                             .replace(r'\(0004\)\(サマリー版\).*', '(0004) Q1 FY3/2024 results update', regex=True)

        # Filter out rows with report titles consisting only of stock codes
        df = df[~df['Downloaded Report'].str.strip().str.contains(r'^\(\d+\)$')]
        df = df[df['Downloaded Report'] != '(0004) アバントグループ(0004)']

        # Extract primary email address if multiple addresses are present
        df['Email'] = df['Email'].str.split(';').str[0]

        # Drop now useless Conversion Page column and reset the index
        df = df.drop(columns=['Conversion Page']).reset_index(drop=True)

        return df

    # Define columns to keep in the DataFrame
    col_to_keep = [
        'User Name',
        'Email',
        'Downloaded Report',
        'Conversion Date',
        'Conversion Page'
        ]

    # Move contents from Japanese columns to English columns
    df['First name'].fillna(df['姓'], inplace=True)
    df['Last name'].fillna(df['名'], inplace=True)
    df['Email'].fillna(df['メールアドレス'], inplace=True)
    df['Profession'].fillna(df['属性'], inplace=True)

    # Create 'User Name' column by combining 'First Name' and 'Last Name'
    df['User Name'] = df['First name'] + ' ' + df['Last name']

    # Keep only selected columns
    df = df[col_to_keep]

    # Filter out all non-disclosed company downloads
    df = df[(df['Email'].str.endswith('@non-disclosedcompany.com') == False) & (df['Email'] != 'company@hotmail.com')]

    # Remove rows with NaN values in any column
    df.replace('nan', np.nan, inplace=True)
    df = df.dropna()

    # Remove test and otherwise unusable rows
    df = df[~((df['Downloaded Report'].str.contains('テスト')) |
              (df['Downloaded Report'] == 'Q2') |
              (df['Conversion Page'].str.contains('non-disclosed link')) |
              (df['Conversion Page'].str.contains('non-disclosed link')))]

    df = pre_cleaning_example_publisher_7(df)

    # Add the Platform, Firm Name, City, Country, Transaction ID and Post Date columns to the DataFrame
    df = df.assign(**{
        'Platform':       'example_publisher_7',
        'Firm Name':      '非公開',
        'City':           '非公開',
        'Country':        '非公開',
        'Transaction ID': '非公開',
        'Post Date':      '2000-12-31 00:00:00 AM'
        })

    # Rename columns for clarity and consistency
    df = df.rename(columns={
        'Conversion Date':   'Read Date',
        'Platform':          'Platform',
        'Firm Name':         'Firm Name',
        'User Name':         'User Name',
        'Email':             'Email',
        'City':              'City',
        'Country':           'Country',
        'Transaction ID':    'Transaction ID',
        'Post Date':         'Post Date',
        'Downloaded Report': 'Report Title'
        })

    def convert_date_example_publisher_7(date_str):
        # Format: YYYY-MM-DD HH:MM:SS AM/PM
        date, _, _ = date_str.split(' ')
        return date

    df[['Read Date', 'Post Date']] = df[['Read Date', 'Post Date']].applymap(convert_date_example_publisher_7)

    # Process DataFrame
    df = map_and_fillna_city(map_and_fillna_country(process_columns(df, remove_duplicates=False)))

    return df

########################################################################################################################

def clean_example_publisher_8(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process a DataFrame containing example_publisher_8 data.

    Arguments:
        df (pandas.DataFrame): DataFrame containing example_publisher_8 data.

    Returns:
        pandas.DataFrame: Cleaned and processed DataFrame.
    """
    # Define columns to keep in the DataFrame
    col_to_keep = [
        'Recipient',
        'Subject',
        'Event Type',
        'Event ID',
        'Event Created Date (Your time zone)',
        'City',
        'Country',
        'Open duration (ms)'
    ]

    df = df[col_to_keep]

    # Filter out all sent emails that where never opened
    df = df[df['Event Type'] == 'OPEN']

    # Filter out all emails that were opened for less than 3 seconds
    df = df[df['Open duration (ms)'].astype(float) > 3000.0]

    # Drop the now useless Event Type and Open duration (ms) columns
    df = df.drop(columns=['Event Type', 'Open duration (ms)'])

    # Filter out all non-disclosed company downloads and reset index to maintain continuous index values
    df = df[(df['Recipient'].str.endswith('@non-disclosedcompany.com') == False) & (df['Recipient'] != 'user@hotmail.com')].reset_index(drop=True)

    # Fill null-values with 非公開 for consistency
    df.fillna('非公開', inplace=True)

    # Add the Platform, User Name, Firm Name and Post Date columns to the DataFrame
    df = df.assign(**{
        'Platform':       'example_publisher_8',
        'User Name':      '非公開',
        'Firm Name':      '非公開',
        'Post Date':      '31/12/2000 00:00'
        })

    # Rename columns for clarity and consistency
    df = df.rename(columns={
        'Event Created Date (Your time zone)': 'Read Date',
        'Platform':                            'Platform',
        'Firm Name':                           'Firm Name',
        'User Name':                           'User Name',
        'Recipient':                           'Email',
        'City':                                'City',
        'Country':                             'Country',
        'Event ID':                            'Transaction ID',
        'Post Date':                           'Post Date',
        'Subject':                             'Report Title'
        })

    def convert_date_example_publisher_8(date_str):
        if len(date_str) == 19:
            date, _ = date_str.split(' ')
            year, month, day = date.split('-')
        elif len(date_str) == 16:
            date, _ = date_str.split(' ')
            day, month, year = date.split('/')
        else:
            day, month, year = date_str.split('/')

        return f"{year}-{int(month):02d}-{int(day):02d}"

    df[['Read Date', 'Post Date']] = df[['Read Date', 'Post Date']].applymap(convert_date_example_publisher_8)

    # Process DataFrame
    df = map_and_fillna_city(map_and_fillna_country(process_columns(df)))

    return df

########################################################################################################################

def preclean_data(df: pd.DataFrame, publisher: str) -> pd.DataFrame:
    """
    Pre-clean data based on the publisher using specific cleaning functions.

    Arguments:
        df (pandas.DataFrame): DataFrame to be pre-cleaned.
        publisher (str): Name of the publisher.

    Returns:
        pandas.DataFrame: Pre-cleaned DataFrame.
    """
    # Dictionary mapping each publisher to its respective cleaning function
    cleaning_functions = {
        'example_publisher_1': clean_example_publisher_1,
        'example_publisher_2': clean_example_publisher_2,
        'example_publisher_3': clean_example_publisher_3,
        'example_publisher_4': clean_example_publisher_4,
        'example_publisher_5': clean_example_publisher_5,
        'example_publisher_6': clean_example_publisher_6,
        'example_publisher_7': clean_example_publisher_7,
        'example_publisher_8': clean_example_publisher_8
    }

    # Get the appropriate cleaning function for the specified publisher
    cleaning_function = cleaning_functions.get(publisher)

    # If a cleaning function is found, apply it to the DataFrame
    if cleaning_function:
        return cleaning_function(df)
    else:
        # Handle unsupported publishers or other cases
        return None

########################################################################################################################

def main(publisher):
    # Get the number of header and footer rows, as well as column names if publisher is example_publisher_4
    header, footer, column_names = get_publisher_info(publisher)

    # Construct input path for uncleaned data
    input_path = os.path.join(RAW_DATA_PATH, '01_Uncleaned', publisher)

    # Set output path to the correct '02_Precleaned Data' subfolder
    output_path = os.path.join(RAW_DATA_PATH, '02_Precleaned', publisher)

    # Create publisher folder if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Generate list of file paths, containing each file in the directory
    file_paths = [os.path.join(input_path, file) for file in os.listdir(input_path)]

    # Read the files into a DataFrame
    master_data = get_data(header, footer, column_names, file_paths)

    # Process the master data
    master_data = preclean_data(master_data, publisher)

    # Save the precleaned master data
    save_precleaned_file(master_data, output_path, publisher)

if __name__ == "__main__":
    main()
