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


class GoogleServicesManager:
    def __init__(self):
        self.__creds = None
        self.__authenticate()
        self.form_service = discovery.build("forms", "v1", credentials=self.__creds)
        self.sheets_service = discovery.build("sheets", "v4", credentials=self.__creds)

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
                    Print(f"Error during token refresh: {e}", type="ERROR")
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
        """Get the details of a form using its ID."""
        result = self.form_service.forms().get(formId=form_id).execute()
        return result

    def __get_form_responses(self, form_id: str) -> ListFormResponsesResponse:
        """Retrieve and print form responses using the form ID."""
        # MIGHT NEED TO HAN
        responses: ListFormResponsesResponse = self.form_service.forms().responses().list(formId=form_id).execute()
        return responses

    def make_copy_of_form(self, form_id: str, new_title: str, add_email: bool) -> Form:
        """Make a copy of a form with the given form ID."""
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
        Print(f"Form ID: {created_form['formId']}", type="INFO")
        Print(f"Form URL to edit: https://docs.google.com/forms/d/{created_form['formId']}/edit", type="INFO")
        Print(f"Form URL to view: {created_form['responderUri']}", type="INFO")
        Print(f"Title = {created_form['info']['title']}", type="INFO")
        # fmt: on
        return created_form

    def create_form_with_questions(self, title: str, questions: List[dict]):
        """Create a form with a title and a list of questions."""
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
        Print(f"Form ID: {created_form['formId']}", type="INFO")
        Print(f"Form URL: https://docs.google.com/forms/d/{created_form['formId']}/edit", type="INFO")
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
            Print("No responses yet", type="WARN")
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


if __name__ == "__main__":

    manager = GoogleServicesManager()

    # Get form details
    form_id = "14vM9XQp7BgHLA6JjtasZoxlFlGfRJdlqrRZqhcw9XHs"
    result = manager.get_form(form_id)
    Print(result)

    # Get form responses
    df = manager.get_form_responses(form_id)
