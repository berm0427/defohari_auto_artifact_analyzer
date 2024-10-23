from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import requests
from google.auth.transport.requests import Request  # This is the correct import

# Authenticate and create a Google Sheet
def upload_to_google_sheets(csv_file_path, json_credentials_path):
    # Define the necessary OAuth scopes for Google Sheets and Drive
    scope = ['https://www.googleapis.com/auth/spreadsheets', 
             'https://www.googleapis.com/auth/drive']

    # Use the provided JSON credentials file for service account authentication
    credentials = Credentials.from_service_account_file(json_credentials_path, scopes=scope)
    client = gspread.authorize(credentials)

    # Create a new Google Sheet and open the first worksheet
    sheet = client.create('Uploaded CSV Data')
    worksheet = sheet.get_worksheet(0)

    # Read CSV into pandas and update Google Sheet
    df = pd.read_csv(csv_file_path)
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    return sheet.id

# Function to download Google Sheets as Excel
def download_google_sheet_as_excel(sheet_id, json_credentials_path):
    # Get the Google Drive API token
    credentials = Credentials.from_service_account_file(json_credentials_path, scopes=['https://www.googleapis.com/auth/drive'])
    
    # Refresh credentials using google.auth.transport.requests.Request
    credentials.refresh(Request())

    # Set the download URL for the Google Sheet as Excel
    download_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

    # Make a request to download the file
    headers = {"Authorization": f"Bearer {credentials.token}"}
    response = requests.get(download_url, headers=headers)

    # Save the file as .xlsx
    if response.status_code == 200:
        with open(r"..\..\output\artifact\defender_log\defender_firewall.xlsx", "wb") as f:
            f.write(response.content)
        print("File downloaded successfully as 'defender_firewall.xlsx'.")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

# Path to your CSV file
csv_file_path = r'..\..\output\artifact\defender_log\Microsoft-Windows-Windows Firewall With Advanced Security%4Firewall.csv'

# Path to your service account JSON credentials file
json_credentials_path = 'pycsvauto-df1c6762bab2.json'

# Upload CSV to Google Sheets and get the sheet ID
sheet_id = upload_to_google_sheets(csv_file_path, json_credentials_path)

# Download the Google Sheet as Excel
download_google_sheet_as_excel(sheet_id, json_credentials_path)
