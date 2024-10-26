import os
import pprint
from typing import List, Tuple, Union

import pandas as pd
import yaml
from Canvas.CanvasService import CanvasAPI
from Canvas.schemas import PageSchema, QuizSchema
from GoogleServices.GoogleServices import GoogleServicesManager
from schemas import *
import json


def read_json_file(file_path: str) -> Dict[str, Any]:
    assert file_path.endswith(".json"), "File must be a JSON file"
    assert os.path.exists(file_path), "File does not exist"
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def read_yml_file(file_path: str) -> Dict[str, Any]:
    assert file_path.endswith(".yml"), "File must be a YAML file"
    assert os.path.exists(file_path), "File does not exist"
    with open(file_path, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


class Grader:
    def __init__(self, course_id: int):
        self.class_info = ClassInfoSchema(**read_yml_file("class_info.yml"))
        self.canvas = CanvasAPI(course_id=course_id)
        self.google = GoogleServicesManager()
        self.module_id_with_presentations = self.canvas.get_module_by_title(self.class_info.presentation_module_title)

    def get_folders_with_team(self, path: str) -> List[str]:
        # Get the folders that contain the team_info.yml file
        folders = []
        for root, dirs, files in os.walk(path):
            if "team_info.yml" in files:
                folders.append(root)
        print("folders = ", folders)
        return folders

    def get_pages_to_create(self, folders: List[str]) -> List[str]:
        # Get the folders that do not have a page in Canvas inside the module self.module_id_with_presentations[id]

        # Get the pages in the module
        pages_created = self.canvas.list_module_items(self.module_id_with_presentations.id)
        print("pages already created = ", pages_created)
        pages_to_create: List[str] = []
        for folder in folders:
            team_info = self.__read_team_info_file(folder + "/team_info.yml")
            team_name = team_info.team_name
            # Check if the page already exists
            page_exists = any([team_name in page.title for page in pages_created])
            if not page_exists:
                pages_to_create.append(folder)
        print("pages to create = ", pages_to_create)
        return pages_to_create

    def grade_presentation_project(self, form_id: str, assignment_id: int, emails: List[str]):
        """Grade the presentation for a group of students, this will read the scores from a Google Forms and update the grades in Canvas"""
        print("Grading presentation project...")
        # Get responses from Google Forms
        df_responses = self.google.get_form_responses(form_id)  # DataFrame
        # fmt: off
        df_responses["Overall grade to this team's Slide deck?"] = pd.to_numeric(df_responses["Overall grade to this team's Slide deck?"], errors='coerce')
        df_responses["Overall grade to this team's Presentation skills?"] = pd.to_numeric(df_responses["Overall grade to this team's Presentation skills?"], errors='coerce')
        df_responses["Overall grade to this team's Research topic and (summary) paper content?"] = pd.to_numeric(df_responses["Overall grade to this team's Research topic and (summary) paper content?"], errors='coerce')
        # fmt: on
        print("responses = ", df_responses["Email"])
        print("\n\n")
        #### PROCESSING ####
        # processing - removing emails that are not in the class list
        students = self.canvas.get_users_in_course()
        student_emails = [student["email"].strip().lower() for student in students]
        print("student_emails = ", student_emails)
        # Remove responses from students not in the class
        df_responses["Email"] = df_responses["Email"].str.strip().str.lower()
        df_responses = df_responses[df_responses["Email"].isin(student_emails)]
        print("Cleaned responses = ", df_responses)
        # fmt: off
        
        # Check if there are repeated emails in the responses
        if df_responses["Email"].duplicated().any():
            print("There are repeated emails in the responses")
            # Print the repeated emails
            print(df_responses[df_responses["Email"].duplicated()])
            # Drop the repeated emails
            df_responses = df_responses.drop_duplicates(subset="Email")
        # TODO: Remove outliers 
        grade = (
            df_responses["Overall grade to this team's Slide deck?"].mean()
            + df_responses["Overall grade to this team's Presentation skills?"].mean()
            + df_responses["Overall grade to this team's Research topic and (summary) paper content?"].mean()
        ) / 3
        # fmt: on
        print("Grade:", grade)
        # Update grades in Canvas
        for student in students:
            if student["email"].strip().lower() in emails:
                self.canvas.update_student_grade(assignment_id, student["id"], grade)
        print("Grading complete")

    def __read_team_info_file(self, path: str, raise_error: bool = True) -> TeamInfo:  # type: ignore
        try:
            data = read_yml_file(path)
            team_info = TeamInfo(**data)
            return team_info
        except Exception as e:
            if raise_error:
                raise e

    def create_multiple_canvas_pages_based_on_folder(self, folders: List[str]) -> List[PageSchema]:
        """Create multiple Canvas pages based on a list of folder paths

        Args:
            folders (List[str]): List of folder paths containing presentation materials

        Returns:
            List[PageSchema]: List of created Canvas page objects

        This function iterates through a list of folder paths and creates a Canvas page
        for each folder by calling create_canvas_page_based_on_folder(). Each folder
        should contain presentation materials like PDFs and team info.
        """
        # Initialize empty list to store created pages
        pages = []

        # Create Canvas page for each folder path in the input list
        for folder in folders:
            pages.append(self.create_canvas_page_based_on_folder(folder))

        # Return list of created Canvas pages
        return pages

    def verify_project_files(self, folder_path: str) -> Tuple[str, Union[TeamInfo, None], List[str]]:
        """Verify all required project files exist and return the absolute folder path, team info, and any errors

        Args:
            folder_path (str): Path to the project folder

        Returns:
            Tuple[str, TeamInfo, List[str]]: Tuple containing (absolute_path, team_info, list_of_errors)
        """
        errors: List[str] = []
        team_info: Union[TeamInfo, None] = None

        # Get absolute folder path
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        abs_folder_path = os.path.join(cur_dir, folder_path)
        abs_folder_path = os.path.abspath(abs_folder_path)

        if not os.path.exists(abs_folder_path):
            errors.append("Folder path does not exist")
            return abs_folder_path, None, errors

        # Check required files exist
        required_files = {
            "presentation.pdf": "Presentation file is missing",
            "paper.pdf": "Paper file is missing",
            "quiz.json": "Quiz file is missing",
            "team_info.yml": "Team info file is missing",
        }

        for file, error_msg in required_files.items():
            file_path = os.path.join(abs_folder_path, file)
            if not os.path.exists(file_path):
                errors.append(error_msg)

        # Try to load and verify team info if yml exists
        team_info_path = os.path.join(abs_folder_path, "team_info.yml")
        if os.path.exists(team_info_path):
            try:
                team_info = self.__read_team_info_file(team_info_path)
            except ValidationError as e:
                error_details = []
                for err in e.errors():
                    field_path = " -> ".join(str(x) for x in err["loc"])
                    error_details.append(f"\tField '{field_path}': {err['msg']}")
                errors.append(f"Invalid team_info.yml:\n" + "\n".join(error_details))
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax in team_info.yml: {str(e)}")
            except Exception as e:
                errors.append(f"Unexpected error reading team_info.yml: {str(e)}")

        # Try to load and verify quiz if json exists
        quiz_path = os.path.join(abs_folder_path, "quiz.json")
        if os.path.exists(quiz_path):
            try:
                quiz_data = read_json_file(quiz_path)
                # Here you would validate quiz_data against your schema
                # For example:
                quiz = QuizSchema(**quiz_data)
            except AssertionError as e:
                errors.append(f"Quiz file error: {str(e)}")
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON syntax in quiz.json: {str(e)}")
            except ValidationError as e:
                error_details = []
                for err in e.errors():
                    field_path = " -> ".join(str(x) for x in err["loc"])
                    error_details.append(f"\tField '{field_path}': {err['msg']}")
                errors.append(f"Invalid quiz.json format:\n" + "\n".join(error_details))
            except Exception as e:
                errors.append(f"Unexpected error reading quiz.json: {str(e)}")

        return abs_folder_path, team_info, errors

    def verify_all_projects(self, folders: List[str]) -> List[Tuple[str, List[str]]]:
        """Verify all projects in the given folders and return a list of folders with their errors.

        Args:
            folders (List[str]): List of folder paths to verify

        Returns:
            List[Tuple[str, List[str]]]: List of tuples containing (folder_path, list_of_errors)
        """
        verification_results = []

        for folder in folders:
            _, _, errors = self.verify_project_files(folder)
            if errors:
                verification_results.append((folder, errors))

        return verification_results

    def create_canvas_page_based_on_folder(self, folder_path: str) -> PageSchema:
        # Verify project files and get absolute path
        folder_path, team_info, errors = self.verify_project_files(folder_path)
        if errors:
            raise ValueError(f"Project verification failed:\n" + "\n".join(f"- {error}" for error in errors))

        if team_info is None:
            raise ValueError("Team info is None")

        # Upload the presentation and paper
        presentation_url = self.canvas.upload_file(folder_path + "/presentation.pdf")
        paper_url = self.canvas.upload_file(folder_path + "/paper.pdf")

        # Create a Canvas page
        team_members_html = "".join([f"<li>{member.name} - {member.email} </li>" for member in team_info.team_members])
        presentation_start_date = team_info.presentation_time.start.strftime("%b %d")
        presentation_start_time = team_info.presentation_time.start.strftime("%I:%M%p")
        presentation_end_time = team_info.presentation_time.end.strftime("%I:%M%p")
        # Add the appropriate suffix to the day
        day = team_info.presentation_time.start.strftime("%d")
        day_int = int(day)
        if 4 <= day_int <= 20 or 24 <= day_int <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day_int % 10 - 1]

        presentation_start_date = presentation_start_date.replace(f" {day}", f" {day_int}{suffix}")

        body = f"""
                <h2 style="color: #2c3e50;">Team Information</h2>
                <p><strong>Team Name:</strong> {team_info.team_name}</p>
                <p><strong>Topic:</strong> {team_info.topic}</p>
                <p><strong>Team Members:</strong></p>
                <ul style="list-style-type: disc; padding-left: 20px;">
                    {team_members_html}
                </ul>
                <p><strong>Github Repo:</strong> <a href="{team_info.github_repo}" style="color: #3498db;">{team_info.github_repo}</a></p>
                <p><strong>Presentation Time:</strong> {presentation_start_date} at {presentation_start_time} - {presentation_end_time}</p>
                <p><strong>Presentation:</strong> <a href="{presentation_url}" style="color: #3498db;">presentation</a></p>
                <p><strong>Paper:</strong> <a href="{paper_url}" style="color: #3498db;">paper</a></p>
        """
        page = self.canvas.create_page(title=team_info.team_name, body=body)
        return page

    def add_google_forms_and_create_quiz(self, page: PageSchema, folder_path: str):

        cur_dir = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.join(cur_dir, folder_path)
        folder_path = os.path.abspath(folder_path)
        assert os.path.exists(folder_path), "Folder path does not exist"
        quiz_path = folder_path + "/quiz.json"
        assert os.path.exists(quiz_path), "Quiz file does not exist"
        # Verify that schema for quiz is good
        team_info_path = folder_path + "/team_info.yml"
        team_info = self.__read_team_info_file(team_info_path)

        old_body = page.body
        # Create a create a google forms for feedback to open at start time and close at end time + 20minutes
        form = self.google.make_copy_of_form(
            "1UwS-2ntDwCXjQWsS0ADsZvDWzV0MMeo6I-mw5zcbVrw",  # FIXME: THis id already has a Question for email, either change ID or remove the question in the code
            f"Feedback for {team_info.team_name}",
        )
        form_url = form["responderUri"]
        quiz = self.canvas.create_quiz_from_file(folder_path + "/quiz.json")
        quiz_url = quiz["html_url"]
        # Add the google form to the page
        body = f"""
            {old_body}
            <p><strong>Feedback Form:</strong> <a href="{form_url}" style="color: #3498db;">Feedback Form</a></p>
            <p><strong>Quiz:</strong> <a href="{quiz_url}" style="color: #3498db;">Quiz</a></p>
        """

        # create canvas quiz based on the quiz file
        return self.canvas.update_page(page.page_id, body=body)

    def remove_feedback_url_and_quiz(self, page: PageSchema):
        old_body: str = page.body  # type: ignore
        # Remove the feedback form and quiz
        body = old_body.split("<p><strong>Feedback Form:</strong>")[0]
        return self.canvas.update_page(page.page_id, body=body)

    def add_images_to_body(self, page: PageSchema, image_paths: List[str]):
        old_body: str = page.body  # type: ignore
        # Add the images to the body
        for image_path in image_paths:
            image_url = self.canvas.upload_file(image_path)
            old_body += f'<img src="{image_url}" alt="Image" >'
        return self.canvas.update_page(page.page_id, body=old_body)


if __name__ == "__main__":
    # UI Requirements:

    # 0. Persistent State
    # Save all the information of the UI and the state in a file (state.json)
    # save the file every time there is a change in the state

    # 1. Course Selection Screen
    #    - Dropdown to select course from Canvas courses
    #    - Input field for course ID
    #    - "Connect" button to initialize grader

    # 2. Project Verification Panel
    #    - File browser to select root folder containing team projects
    #    - "Verify All Projects" button
    #    - Results display showing:
    #      * Progress bar during verification
    #      * Table of verification results with folder paths and errors
    #      * Color coding for pass/fail status
    #    - Option to export verification results

    # 3. Canvas Pages Management
    #    - Table showing all folders and their current Canvas page status
    #    - Checkboxes to select which pages to create/update
    #    - Preview button to see page content before creation
    #    - Bulk actions for creating multiple pages
    #    - Status indicators for page creation progress

    # 4. Forms & Quiz Management
    #    - Table of all pages with toggles for:
    #      * Adding feedback forms
    #      * Adding quizzes
    #      * Removing forms/quizzes
    #    - Scheduling options for form availability
    #    - Quiz preview functionality
    #    - Batch operations for forms/quizzes

    # Sample Implementation
    grader = Grader(course_id=15319)
    folders = grader.get_folders_with_team(".")

    # Project Verification Step
    verification_results = grader.verify_all_projects(folders)
    if verification_results:
        # UI would display this in a formatted table rather than console
        print("\nProject Verification Failures:")
        for folder, errors in verification_results:
            print(f"\nFolder: {folder}")
            for error in errors:
                print(f"  - {error}")
        raise SystemExit("Please fix the above errors before continuing.")

    # Page Creation Step
    # UI would show this as a table with checkboxes
    pages_to_create = grader.get_pages_to_create(folders)
    pages = grader.create_multiple_canvas_pages_based_on_folder(pages_to_create)

    # Forms & Quiz Management
    # UI would show a table with toggles for each action
    for page, folder_path in zip(pages, pages_to_create):
        grader.add_google_forms_and_create_quiz(page, folder_path=folder_path)

    # Cleanup Step
    # UI would have batch operations and individual toggles
    for page in pages:
        grader.remove_feedback_url_and_quiz(page)
