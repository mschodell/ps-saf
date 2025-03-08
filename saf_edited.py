import requests
import os
import pandas as pd
from requests.auth import HTTPBasicAuth
import pygsheets
import base64


def main():
    # GOOGLE SHEETS SETUP
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

    # Spreadsheet key for where the data goes
    spreadsheet_key = "1t8qYEmbyaB8RvgSUJPFoZfvPHx7NUE7sN82ZNImwyPI"

    # API credentials
    token = os.getenv("TOKEN")
    current_form = "41393"

    # GET SUBMISSION RECORDS FOR CURRENT FORM
    endpoint_url = f"http://secure.infosnap.com/api/v1/publishedactions/{current_form}/submissionrecords"
    response = requests.get(endpoint_url, auth=HTTPBasicAuth(token, ""))

    if response.status_code != 200:
        print(f"❌ API Request Failed! Status Code: {response.status_code}")
        print("Response Text:", response.text)
        exit(1)

    result = response.json()

    # Validate the presence of 'metaData'
    if 'metaData' not in result or 'pageCount' not in result['metaData']:
        print("❌ Error: 'metaData' or 'pageCount' missing from API response.")
        print("Full Response:", result)
        exit(1)
    
    pages = result['metaData']['pageCount']
    all_data = []
    
    for page in range(1, pages + 1):
        endpoint_url = f"http://secure.infosnap.com/api/v1/publishedactions/{current_form}/submissionrecords?page={page}"
        response = requests.get(endpoint_url, auth=HTTPBasicAuth(token, ""))
        
        if response.status_code != 200:
            print(f"❌ API Request Failed on page {page}! Status Code: {response.status_code}")
            print("Response Text:", response.text)
            continue  # Skip to the next page
        
        data = response.json()
        all_data.extend(data.get('records', []))
    
    if not all_data:
        print("❌ No valid data retrieved from API.")
        exit(1)
    
    df = pd.json_normalize(all_data)
    df = df.applymap(lambda x: tuple(x) if isinstance(x, list) else x)
    df = df.fillna('')
    df_filtered = df[df['status'] != 'Discarded']
    df_columns = pd.DataFrame(df_filtered.columns, columns=['Columns'])

    spreadsheet = gc.open_by_key(spreadsheet_key)
    print("✅ Opened Google Sheet")

    sheet = spreadsheet.worksheet('title', "Columns")
    sheet.set_dataframe(df_columns, "A1")
    
    df_filtered = df_filtered[['id', 'firstName', 'lastName', 'dateOfBirth', 'grade', 'dataItems.adm_OneAppID', 'dataItems.adm_Qualified_MR']]
    df_filtered['dateOfBirth'] = pd.to_datetime(df_filtered['dateOfBirth']).dt.strftime('%m/%d/%Y')
    
    sheet = spreadsheet.worksheet('title', "Submissions")
    sheet.set_dataframe(df_filtered, "A1")

if __name__ == "__main__":
    main()
