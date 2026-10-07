# imports our functions from scrape.py so we can call the functions from here
'''Note: import * production code එකට හොඳ පුරුද්දක් නෙවෙයි — මොන නම් මොනවද ආවේ කියලා පේන්නේ නෑ, ඒ නිසා name collision එකක් ආවොත් debug කරන්න අමාරුයි. from scrape import league_table, top_scorers කියලා explicit කරන එක තමයි හොඳ.'''
# from scrape import *
from scrape import league_table, top_scorers
from api_ingest import premier_league_teams

import os
from dotenv import load_dotenv
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


# reads variables from the .env file into the environment
load_dotenv()

# list of functions to be called and pushed to azure blob storage
functions = [league_table,top_scorers,premier_league_teams]

def to_blob(func):

    '''
    Converts the output of a given function to Parquet format and uploads it to Azure Blob Storage.
    Args:
        func (function): The function that retrieves data to be processed and uploaded.
    Returns:
        None
    This function takes a provided function, calls it to obtain data, and then converts the data into
    an Arrow Table. The Arrow Table is serialized into Parquet format and uploaded to an Azure Blob
    Storage container specified in the function. The function's name is used as the blob name.
    Example:
        Consider the function "top_scorers". Calling "to_blob(top_scorers)" will process the output
        of "top_scorers", convert it to Parquet format, and upload it to Azure Blob Storage.
        '''

    file_name = func.__name__
    # this will run the function which passes as a parameter to the to_blob function and return the dataframe output
    df = func()


    # Convert DataFrame to Arrow Table
    table = pa.Table.from_pandas(df)
    # Serialize Arrow Table to Parquet format in memory
    parquet_buffer = BytesIO()
    # Write the Arrow Table to the Parquet buffer
    pq.write_table(table, parquet_buffer)

    # Upload to Azure Blob Storage
    # refer to image "azure_blob_storage_access_key.png"
    '''
    hardcoding it isn't OK. Never put a connection string with an AccountKey in source code. Your repo has no commits yet, so it hasn't been pushed to GitHub. That's the moment to fix it.

    Why it's a problem

    The AccountKey is effectively a password for the whole storage account. It gives full read, write and delete access, not just this container.

    Once it's committed, it stays in git history even if you delete it later.

    Bots scan public GitHub repos for Azure keys and find them within minutes.

    images/azure_blob_storage_access_key.png is a screenshot of the Azure access key page. Check whether it shows the key value, and don't commit it if it does.
    
    How real projects handle it

    1	.env file, loaded with python-dotenv, listed in .gitignore	
    Best for : Local dev and learning projects

    2	Environment variables set by the platform (GitHub Actions secrets, Databricks secret scopes, Azure App Service settings)	
    Best for : CI/CD and jobs

    3	Azure Key Vault, with the app authenticating through Managed Identity or DefaultAzureCredential	
    Best for: Production



    The best production setup has no key at all. You give the app's identity the "Storage Blob Data Contributor" role on the storage account, then connect like this:
    
    from azure.identity import DefaultAzureCredential
    BlobServiceClient("https://testblobsportsanalytics.blob.core.windows.net", credential=DefaultAzureCredential())

    There's nothing to leak or rotate. Locally it uses your az login.

    
    What I'd do for this project (level 1)

    Rotate the key now. In the Azure portal, open Storage account → Access keys → Rotate key1. I've read the key in this session, and it's also in your OneDrive, so treat it as exposed.

    Create a .env file containing AZURE_STORAGE_CONNECTION_STRING=....
    Add .env to .gitignore. It isn't listed there right now.

    In the script, replace line 45 with os.getenv("AZURE_STORAGE_CONNECTION_STRING") after load_dotenv(). python-dotenv is already in your requirements.txt.
    
    Commit a .env.example with placeholder values so others know which variables to set.

    '''
    # the connection string now lives in .env (see .env.example), never in the code
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is not set. Copy key from Azure portal -> Storage account -> Access keys -> Connection string and fill it in.")
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    container_name = "testtech"
    blob_name = f"{file_name}.parquet"
    container_client = blob_service_client.get_container_client(container_name)

    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(parquet_buffer.getvalue(), overwrite=True)
    print(f"{blob_name} successfully updated")

# Call the function for each function in the list
# (guarded so that importing this file from run_pipeline.py doesn't trigger an upload)
if __name__ == "__main__":
    for items in functions:
        to_blob(items)