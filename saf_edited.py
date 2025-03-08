import requests
import os
import pandas as pd
from requests.auth import HTTPBasicAuth
import pygsheets

def main():
    #GOOGLESHEETS SET UP
    # Decode the Base64-encoded credentials and save as a JSON file
    CREDENTIALS_FILE = "client_secret.json"
    base64_credentials = os.getenv("GSHEETS_BASE64")
    
    if base64_credentials:
        try:
            with open(CREDENTIALS_FILE, "w") as f:
                f.write(base64.b64decode(base64_credentials).decode())
            print("✅ Credentials file decoded successfully.")
        except Exception as e:
            print("❌ Error decoding credentials:", e)
            exit(1)
    else:
        print("❌ Error: GSHEETS_BASE64 environment variable not found!")
        exit(1)
    
    # Authenticate with Google Sheets using the decoded file
    gc = pygsheets.authorize(service_file=CREDENTIALS_FILE)

    #spreadsheet key for where the data goes
    spreadsheet_key = "1t8qYEmbyaB8RvgSUJPFoZfvPHx7NUE7sN82ZNImwyPI"

    # API credentials
    # Read the token from the file
    token = os.getenv("TOKEN")

    #current form ID
    current_form = "41393"
    
    #GET SUBMISSION RECORDS FOR CURRENT FORM
    #get number of pages
    endpoint_url = "http://secure.infosnap.com/api/v1/publishedactions/" + str(current_form) + "/submissionrecords"
    response = requests.get(endpoint_url, auth=HTTPBasicAuth(token,""))
    result = response.json()
    pages = result['metaData']['pageCount']
    
    #iterate through pages  collecting data
    all_data = []
    page = 1
    
    while page <= pages:
        endpoint_url = "http://secure.infosnap.com/api/v1/publishedactions/" + str(current_form) + "/submissionrecords?page=" + str(page)
        response = requests.get(endpoint_url, auth=HTTPBasicAuth(token,""))
        data = response.json()
        all_data.extend(data['records'])
        page += 1
    
    df = pd.json_normalize(all_data)
    
    # convert the lists to tuples
    df = df.applymap(lambda x: tuple(x) if isinstance(x, list) else x)
        
    # replace NaN values with blank values
    df = df.fillna('')
    
    # Exclude rows where Status is "Discarded"
    df_filtered = df[df['status'] != 'Discarded']
    
    #get columns
    df_columns = pd.DataFrame(df_filtered.columns, columns=['Columns'])
    
    spreadsheet = gc.open_by_key(spreadsheet_key)
    print("Opened google sheet")
    
    #print all columns
    sheet = spreadsheet.worksheet('title',"Columns")
    sheet.set_dataframe(df_columns,"A1")
    
    #keep only certain columns
    df_filtered = df_filtered[['id', 'firstName', 'lastName', 'dateOfBirth', 'grade', 'dataItems.adm_OneAppID', 'dataItems.adm_Qualified_MR']]  # Replace with the columns you want to keep
    
    df_filtered['dateOfBirth'] = pd.to_datetime(df_filtered['dateOfBirth']).dt.strftime('%m/%d/%Y')
    
    #ADD TO GOOGLE SHEET
    sheet = spreadsheet.worksheet('title',"Submissions")
    sheet.set_dataframe(df_filtered,"A1")

if __name__ == "__main__":
    main()
