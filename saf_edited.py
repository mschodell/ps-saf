import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
import pygsheets

def main():
    #GOOGLESHEETS SET UP
    gc = pygsheets.authorize(service_file='/Users/lucyschodell/Desktop/willow/fiery-tribute-453120-f9-3ed41865cd67.json')

    #spreadsheet key for where the data goes
    spreadsheet_key = "1t8qYEmbyaB8RvgSUJPFoZfvPHx7NUE7sN82ZNImwyPI"

    # API credentials
    # Read the token from the file
    token = os.getenv("token")

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
    
    df2 = pd.json_normalize(all_data)
    
    # convert the lists to tuples
    df2 = df2.applymap(lambda x: tuple(x) if isinstance(x, list) else x)
    
    # count the number of unique values in each column
    unique_counts = df2.nunique()
    
    # replace NaN values with blank values
    df2 = df2.fillna('')
    
    # Exclude rows where Status is "Discarded"
    df_filtered = df2[df2['status'] != 'Discarded']
    
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
