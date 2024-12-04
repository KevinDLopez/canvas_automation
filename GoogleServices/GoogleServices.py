import os.path
import pprint
import sys
from typing import Literal, Optional, TypedDict, List, Dict, Union
from googleapiclient import discovery
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pandas as pd
import requests
import gspread
from gspread.spreadsheet import Spreadsheet
from gspread.worksheet import Worksheet

from GoogleServices.schemas import (
    BatchUpdateFormResponse,
    Form,
    Item,
    ListFormResponsesResponse,
    Request as RequestType,
    Response,
)
from Logging import Print

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

base_path = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.abspath(".")

client_secrets_path = os.path.join(base_path, "client_secrets.json")
token_path = os.path.join(base_path, "token.json")


def get_id_from_url(url: str) -> str:
    """Extract the spreadsheet ID from a Google Sheets URL.

    Args:
        url (str): Google Sheets URL

    Returns:
        str: Spreadsheet ID

    Example:
        >>> url = "https://docs.google.com/spreadsheets/d/1tuuIobh2R4KQJBxCPR60E0EFVW_jr9_l6Aaj3lx6qaQ/edit?gid=407629335"
        >>> get_id_from_url(url)
        '1tuuIobh2R4KQJBxCPR60E0EFVW_jr9_l6Aaj3lx6qaQ'
    """
    # Split on /d/ and take the second part
    parts = url.split("/d/")

    # Split on first / after the ID and take the first part
    id_part = parts[1].split("/")[0]
    return id_part


class GoogleServicesManager:
    """A manager class for interacting with various Google services including Forms, Sheets and Drive.

    This class provides methods to:
    - Authenticate with Google services using OAuth2
    - Work with Google Forms (create, copy, get responses)
    - Work with Google Sheets (read, write, update worksheets)
    - Access Google Drive files

    The manager handles authentication automatically on initialization and maintains
    credentials for subsequent API calls.

    Attributes:
        form_service: Google Forms API service instance
        sheets_service: Google Sheets API service instance
        gspread_client: Authorized gspread client for spreadsheet operations

    """

    def __init__(self):
        self.__creds = None
        self.__authenticate()
        self.form_service = discovery.build("forms", "v1", credentials=self.__creds)
        self.sheets_service = discovery.build("sheets", "v4", credentials=self.__creds)
        self.gspread_client = gspread.authorize(self.__creds)  # type: ignore

    # Add these new methods for gspread functionality
    def open_spreadsheet(self, spreadsheet_name):
        """
        Open a spreadsheet by name

        Args:
            spreadsheet_name (str): Name of the spreadsheet

        Returns:
            gspread.Spreadsheet: Spreadsheet object
        """
        return self.gspread_client.open(spreadsheet_name)

    def read_worksheet(self, worksheet: Worksheet):
        """
        Read all values from a worksheet

        Args:
            worksheet (gspread.Worksheet): Worksheet object to read from

        Returns:
            list: List of rows containing worksheet data
        """
        return worksheet.get_all_records()

    def get_spreadsheets(self):
        """
        Get all spreadsheets from Google Drive

        Returns:
            list: List of spreadsheets
        """
        return self.gspread_client.list_spreadsheet_files()

    def open_spreadsheet_by_id(self, spreadsheet_id):
        """
        Open a spreadsheet by its ID

        Args:
            spreadsheet_id (str): The ID of the spreadsheet (can be extracted from the URL)

        Returns:
            gspread.Spreadsheet: Spreadsheet object
        """
        return self.gspread_client.open_by_key(spreadsheet_id)

    def __authenticate(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists(token_path):
            self.__creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.__creds or not self.__creds.valid:
            if self.__creds and self.__creds.expired and self.__creds.refresh_token:
                try:
                    if self.__creds and self.__creds.expired and self.__creds.refresh_token:
                        self.__creds.refresh(Request())
                    else:
                        raise Exception("Invalid credentials")
                except Exception as e:
                    Print(f"Error during token refresh: {e}", log_type="ERROR")
                    if os.path.exists(token_path):
                        os.remove(token_path)
                    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
                    self.__creds = flow.run_local_server(port=0)
                    # Save the credentials for the next run
                    with open(token_path, "w") as token:
                        token.write(self.__creds.to_json())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
                self.__creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, "w") as token:
                token.write(self.__creds.to_json())

    def get_form(self, form_id: str) -> Form:
        """Get the details of a Google Form using its ID.

        Args:
            form_id (str): The ID of the form to retrieve

        Returns:
            Form: A Form object containing the form details including:
                - formId: The unique identifier of the form
                - info: Basic form information like title
                - items: List of form items/questions
                - linkedSheetId: ID of linked response spreadsheet
                - responderUri: URL for form respondents
                - revisionId: Form revision identifier
                - settings: Form settings configuration

        Example:
            >>> google_service = GoogleServices()
            >>> form = google_service.get_form("abc123xyz")
            >>> print(form["info"]["title"])
            "My Survey Form"
        """
        result = self.form_service.forms().get(formId=form_id).execute()
        return result

    def __get_form_responses(self, form_id: str) -> ListFormResponsesResponse:
        """Retrieve and print form responses using the form ID."""
        # MIGHT NEED TO HAN
        responses: ListFormResponsesResponse = self.form_service.forms().responses().list(formId=form_id).execute()
        return responses

    def make_copy_of_form(self, form_id: str, new_title: str, add_email: bool) -> Form:
        """Make a copy of a Google Form with the given form ID and customize it.

        This method creates a copy of an existing form template and optionally adds an email field
        at the beginning. All other questions from the template form are copied over.

        Args:
            form_id (str): The ID of the template form to copy
            new_title (str): The title for the new form copy
            add_email (bool): Whether to add an email field at the start of the form

        Returns:
            Form: The created form object containing details like formId, title and URLs

        Example:
            >>> google_service = GoogleServices()
            >>> template_id = "1234abcd..."
            >>> new_form = google_service.make_copy_of_form(
            ...     form_id=template_id,
            ...     new_title="Student Survey 2024",
            ...     add_email=True
            ... )
            >>> print(f"Created form with ID: {new_form['formId']}")
            Created form with ID: 5678efgh...
            >>> print(f"Form URL: {new_form['responderUri']}")
            Form URL: https://docs.google.com/forms/d/5678efgh.../viewform
        """
        template_form = self.get_form(form_id)  # Get the details from the template

        new_form = {"info": {"title": new_title}}
        created_form: Form = self.form_service.forms().create(body=new_form).execute()
        Print("created_form", created_form)

        create_items: List[RequestType] = []
        j = 0
        if add_email:
            create_items.append(
                {
                    "createItem": {
                        "item": {
                            "title": "Email",
                            "questionItem": {
                                "question": {
                                    "textQuestion": {"paragraph": False},
                                    "required": True,
                                },
                            },
                            "description": "Enter your CSULB email address, e.g., First.Last.001@student.csulb.edu",
                        },
                        "location": {"index": j},
                    }
                }  # type: ignore
            )
            j += 1
        for i, item in enumerate(template_form["items"]):
            create_items.append({"createItem": {"item": item, "location": {"index": i + j}}})

        batch_update_request = {"requests": create_items}

        # Execute the batch update
        batch_update_response: BatchUpdateFormResponse = (
            self.form_service.forms().batchUpdate(formId=created_form["formId"], body=batch_update_request).execute()
        )
        Print("batch_update_response", batch_update_response)

        # Print the form ID and URL
        # fmt: off
        Print(f"Form ID: {created_form['formId']}", log_type="INFO")
        Print(f"Form URL to edit: https://docs.google.com/forms/d/{created_form['formId']}/edit", log_type="INFO")
        Print(f"Form URL to view: {created_form['responderUri']}", log_type="INFO")
        Print(f"Title = {created_form['info']['title']}", log_type="INFO")
        # fmt: on
        return created_form

    def create_form_with_questions(self, title: str, questions: List[dict]):
        """Create a form with a title and a list of questions.

        Args:
            title (str): The title of the form to create
            questions (List[dict]): List of question dictionaries, where each dict contains:
                - title (str): The question text
                - required (bool): Whether the question is required
                - type (str): The question type (e.g. 'textQuestion', 'choiceQuestion')
                - options (dict): Type-specific configuration for the question

        Returns:
            BatchUpdateFormResponse: Response from the form creation API containing details
                about the created form and questions

        Example:
            >>> questions = [
            ...     {
            ...         "title": "What is your name?",
            ...         "required": True,
            ...         "type": "textQuestion",
            ...         "options": {"paragraph": False}
            ...     },
            ...     {
            ...         "title": "Select your favorite color",
            ...         "required": False,
            ...         "type": "choiceQuestion",
            ...         "options": {
            ...             "choices": [
            ...                 {"value": "Red"},
            ...                 {"value": "Blue"},
            ...                 {"value": "Green"}
            ...             ]
            ...         }
            ...     }
            ... ]
            >>> form = google_services.create_form_with_questions("Survey Form", questions)
        """
        # Create the form with just the title
        form = {"info": {"title": title}}

        created_form = self.form_service.forms().create(body=form).execute()

        # Define the batch update request to add questions
        form_questions: List[RequestType] = []
        for index, question in enumerate(questions):
            form_questions.append(
                {
                    "createItem": {
                        "item": {
                            "title": question["title"],
                            "questionItem": {
                                "question": {  # type: ignore
                                    "required": question["required"],
                                    question["type"]: question["options"],
                                },
                            },
                        },
                        "location": {"index": index},
                    }
                }
            )

        batch_update_request = {"requests": form_questions}

        # Execute the batch update
        batch_update_response: BatchUpdateFormResponse = (
            self.form_service.forms().batchUpdate(formId=created_form["formId"], body=batch_update_request).execute()
        )
        Print("batch_update_response", batch_update_response)

        # Print the form ID and URL
        Print(f"Form ID: {created_form['formId']}", log_type="INFO")
        Print(f"Form URL: https://docs.google.com/forms/d/{created_form['formId']}/edit", log_type="INFO")
        return batch_update_response

    def get_form_responses(self, form_id: str) -> Optional[pd.DataFrame]:
        form_data = self.get_form(form_id)  # questions are in form_data['questions']
        id_to_question: Dict[str, str] = {}
        for item in form_data["items"]:
            if "questionItem" in item:
                question = item["questionItem"]["question"]
                id_to_question[question["questionId"]] = item["title"]
            if "questionGroupItem" in item:
                for question in item["questionGroupItem"]["questions"]:
                    id_to_question[question["questionId"]] = question["rowQuestion"]["title"]

        data = self.__get_form_responses(form_id)  # Generate pandas dataframe
        rows = []
        if "responses" not in data:
            Print("No responses yet", log_type="WARN")
            return None
        for response in data["responses"]:
            # Print(response)
            row = {
                "responseId": response["responseId"],
                "createTime": response["createTime"],
                "lastSubmittedTime": response["lastSubmittedTime"],
            }
            for question_id, answer_data in response["answers"].items():
                row[id_to_question[question_id]] = answer_data["textAnswers"]["answers"][0]["value"]
            rows.append(row)

        df = pd.DataFrame(rows)
        return df

    def disable_form(self, form_id: str):
        # THIS DOES NOT WORK
        """Disable a form by stopping it from accepting responses."""
        if not self.__creds:
            raise Exception("Not authenticated")

        url = f"https://forms.googleapis.com/v1/forms/{form_id}:batchUpdate"
        headers = {"Authorization": f"Bearer {self.__creds.token}", "Content-Type": "application/json"}
        body = {
            "requests": [
                {"updateSettings": {"settings": {"acceptingResponses": False}, "updateMask": "acceptingResponses"}}
            ]
        }

        # Debugging information
        Print("URL:", url)
        Print("Headers:", headers)
        Print("Body:", body)

        response = requests.post(url, headers=headers, json=body)

        # More debugging information
        Print("Response Status Code:", response.status_code)
        Print("Response Content:", response.content.decode("utf-8"))

        response.raise_for_status()
        return response.json()

    def update_worksheet(self, worksheet: Worksheet, data: list, range_name: Optional[str] = None):
        """
        Update values in a worksheet

        Args:
            worksheet (gspread.Worksheet): Worksheet object to update
            data (list): List of rows to update
            range_name (str, optional): A1 notation range to update. If None, updates from A1
        """
        if range_name:
            worksheet.update(range_name=range_name, values=data)
        else:
            worksheet.update(values=data)

    def update_worksheet_from_records(self, worksheet: Worksheet, records: list[dict], append_only: bool = False):
        """
        Update or append records to a worksheet, clearing existing content when not appending

        Args:
            worksheet (gspread.Worksheet): The worksheet to update
            records (list[dict]): List of dictionary records to update/append
            append_only (bool): If True, only appends new records. If False, clears and rewrites worksheet

        Returns:
            None
        """
        if not records:
            return

        # Get headers from the first record
        headers = list(records[0].keys())

        # Convert records to rows format
        rows = [headers] if not append_only else []
        for record in records:
            rows.append([record[key] for key in headers])

        if not append_only:
            # Clear the existing content before updating
            worksheet.clear()

        if append_only:
            worksheet.append_rows(rows)
        else:
            worksheet.update(values=rows)


if __name__ == "__main__":

    manager = GoogleServicesManager()

    spreadsheet = manager.open_spreadsheet_by_id("1tuuIobh2R4KQJBxCPR60E0EFVW_jr9_l6Aaj3lx6qaQ")
    worksheet = spreadsheet.get_worksheet(1)
    worksheet_records = manager.read_worksheet(worksheet)
