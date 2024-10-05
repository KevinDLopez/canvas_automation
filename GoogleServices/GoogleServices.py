import os.path
import pprint
from typing import Literal, TypedDict, List, Dict, Union
from googleapiclient import discovery
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from GoogleServices.schemas import (
    BatchUpdateFormResponse,
    Form,
    Item,
    ListFormResponsesResponse,
    Request as RequestType,
    Response,
)

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"


class GoogleServicesManager:
    def __init__(self):
        self.__creds = None
        self.__authenticate()
        self.form_service = discovery.build("forms", "v1", credentials=self.__creds)
        self.sheets_service = discovery.build("sheets", "v4", credentials=self.__creds)

    def __authenticate(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists("token.json"):
            self.__creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.__creds or not self.__creds.valid:
            if self.__creds and self.__creds.expired and self.__creds.refresh_token:
                try:
                    if (
                        self.__creds
                        and self.__creds.expired
                        and self.__creds.refresh_token
                    ):
                        self.__creds.refresh(Request())
                    else:
                        raise Exception("Invalid credentials")
                except Exception as e:
                    print(f"Error during token refresh: {e}")
                    if os.path.exists("token.json"):
                        os.remove("token.json")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "client_secrets.json", SCOPES
                    )
                    self.__creds = flow.run_local_server(port=0)
                    # Save the credentials for the next run
                    with open("token.json", "w") as token:
                        token.write(self.__creds.to_json())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "client_secrets.json", SCOPES
                )
                self.__creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(self.__creds.to_json())

    def get_form(self, form_id: str) -> Form:
        """Get the details of a form using its ID."""
        result = self.form_service.forms().get(formId=form_id).execute()
        return result

    def get_form_responses(self, form_id: str) -> ListFormResponsesResponse:
        """Retrieve and print form responses using the form ID."""
        # MIGHT NEED TO HAN
        responses: ListFormResponsesResponse = (
            self.form_service.forms().responses().list(formId=form_id).execute()
        )
        return responses

    def make_copy_of_form(self, form_id: str):
        """Make a copy of a form with the given form ID."""
        form = self.get_form(form_id)

        new_form = {"info": {"title": form["info"]["title"]}}
        created_form: Form = self.form_service.forms().create(body=new_form).execute()
        print("created_form", created_form)

        create_items: List[RequestType] = []
        for i, item in enumerate(form["items"]):
            create_items.append(
                {"createItem": {"item": item, "location": {"index": i}}}
            )

        batch_update_request = {"requests": create_items}

        # Execute the batch update
        batch_update_response: BatchUpdateFormResponse = (
            self.form_service.forms()
            .batchUpdate(formId=created_form["formId"], body=batch_update_request)
            .execute()
        )
        print("batch_update_response", batch_update_response)

        # Print the form ID and URL
        # fmt: off
        print(f"Form ID: {created_form['formId']}")
        print(f"Form URL to edit: https://docs.google.com/forms/d/{created_form['formId']}/edit")
        print(f"Form URL to view: {created_form['responderUri']}")
        print(f"Title = {created_form['info']['title']}")
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
            self.form_service.forms()
            .batchUpdate(formId=created_form["formId"], body=batch_update_request)
            .execute()
        )
        print("batch_update_response", batch_update_response)

        # Print the form ID and URL
        print(f"Form ID: {created_form['formId']}")
        print(
            f"Form URL: https://docs.google.com/forms/d/{created_form['formId']}/edit"
        )
        return batch_update_response


if __name__ == "__main__":

    manager = GoogleServicesManager()

    # Get form details
    form_id = "14vM9XQp7BgHLA6JjtasZoxlFlGfRJdlqrRZqhcw9XHs"
    result = manager.get_form(form_id)
    print(result)

    manager.make_copy_of_form("14vM9XQp7BgHLA6JjtasZoxlFlGfRJdlqrRZqhcw9XHs")
