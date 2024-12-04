import os
import sys
import gspread
from google.oauth2.service_account import Credentials


class GoogleSheets:
    def __init__(self, credentials_path):
        """
        Initialize Google Sheets connection

        Args:
            credentials_path (str): Path to your service account credentials JSON file
        """
        self.scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        self.creds = Credentials.from_service_account_file(credentials_path, scopes=self.scope)
        self.client = gspread.authorize(self.creds)

    def open_spreadsheet(self, spreadsheet_name):
        """
        Open a spreadsheet by name

        Args:
            spreadsheet_name (str): Name of the spreadsheet

        Returns:
            gspread.Spreadsheet: Spreadsheet object
        """
        return self.client.open(spreadsheet_name)

    def read_worksheet(self, spreadsheet, worksheet_name):
        """
        Read all values from a worksheet

        Args:
            spreadsheet (gspread.Spreadsheet): Spreadsheet object
            worksheet_name (str): Name of the worksheet

        Returns:
            list: List of rows containing worksheet data
        """
        worksheet = spreadsheet.worksheet(worksheet_name)
        return worksheet.get_all_records()


if __name__ == "__main__":
    base_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.abspath(".")
    credentials_path = os.path.join(base_path, "client_secrets.json")
    print("**", credentials_path)
    gs = GoogleSheets(credentials_path)
    spreadsheet = gs.open_spreadsheet("Test")
    print(gs.read_worksheet(spreadsheet, "Sheet1"))
