# Import libraries
import warnings
import os
import datetime
import pandas as pd
from src.params import CLEAN_DATA_PATH, CUSTOMERS

warnings.filterwarnings("ignore")

########################################################################################################################

def save_readership_file(df: pd.DataFrame, output_path: str, customer: str) -> None:
    """
    Save readership DataFrame to a file.

    Arguments:
        df (pandas.DataFrame):  DataFrame to be saved.
        output_path (str):      Path to the directory where the file will be saved.
        customer (str):         Name of the customer.

    Returns:
        None
    """
    # Construct output file name, example: '2024-03-07 Factset Precleaned.xlsx'
    output_file = f'{customer} Readership File.xlsx'
    # Save file in folder '03_Customers/Customer/01_Clean Data'
    df.to_excel(os.path.join(output_path, output_file), index=False)

    return None

########################################################################################################################

def main():
    for customer in CUSTOMERS.keys():
        # Construct input path for clean data
        input_path = os.path.join(CLEAN_DATA_PATH, customer, '01_Clean Data')

        # Construct output path for readership file
        output_path = os.path.join(CLEAN_DATA_PATH, customer)

        # Construct input path for precleaned data
        file_paths = [os.path.join(input_path, file) for file in os.listdir(input_path)]

        # Read the input files into DataFrames and store them in a list
        dfs = [pd.read_excel(file) for file in file_paths]

        # Concatonate all dfs in the list into a single DataFrame
        readership = pd.concat(dfs, ignore_index=True).sort_values(by='Read Date').reset_index(drop=True)

        # Drop unnecessary Report Title column
        readership = readership.drop(columns=['Report Title'])

        # Add column Updated On with the current day
        readership = readership.assign(**{'Updated On': pd.to_datetime(datetime.datetime.now().strftime('%Y-%m-%d'))})

        # Retain only date portion
        readership[['Post Date', 'Updated On']] = readership[['Post Date', 'Updated On']].apply(lambda x: x.dt.date)

        # Save the readership file
        save_readership_file(readership, output_path, customer)

if __name__ == "__main__":
    main()
