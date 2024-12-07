import os
import pprint
from typing import List, Tuple, Union

from matplotlib import pyplot as plt
import pandas as pd
import yaml
from Canvas.CanvasService import CanvasAPI
from Canvas.schemas import PageSchema, QuizSchema
from GoogleServices.GoogleServices import GoogleServicesManager
from Logging import Print
from schemas import *
import json
from gspread.worksheet import Worksheet


def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read a JSON file and return its contents as a dictionary"""
    assert file_path.endswith(".json"), "File must be a JSON file"
    assert os.path.exists(file_path), f"File does not exist, {file_path}"
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def read_yml_file(file_path: str) -> Dict[str, Any]:
    """Read a YAML file and return its contents as a dictionary"""
    assert file_path.endswith(".yml"), "File must be a YAML file"
    assert os.path.exists(file_path), "File does not exist, YML"
    with open(file_path, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


def create_image(responses: pd.DataFrame, output_path: str):
    """
    This function takes a DataFrame of responses and an output path to save the generated image.

    Parameters:
        responses (pd.DataFrame): DataFrame containing student data
        output_path (str): Path where the image will be saved

    Example:
        >>> import pandas as pd
        >>> responses = pd.DataFrame({
        ...     'Student': ['Alice', 'Bob', 'Charlie'],
        ...     'Score': [85, 90, 78]
        ... })
        >>> output_path = 'output/grades_chart.png'
        >>> create_image(responses, output_path)
    """
    plt.figure(figsize=(15, 4))
    plt.subplot(1, 3, 1)
    plt.hist(
        responses["Overall grade to this team's Slide deck?"].dropna(), bins=10, edgecolor="black", color="skyblue"
    )
    plt.title("Histogram of Overall Grades Slide deck", fontsize=12)
    plt.xlabel("Overall Slide deck Grade", fontsize=10)
    plt.ylabel("Frequency", fontsize=10)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.grid(True, linestyle="--", alpha=0.7)

    # Overall grade to this team's Research topic and (summary) paper content?
    # Overall grade to this team's Presentation skills?
    plt.subplot(1, 3, 2)
    plt.hist(
        responses["Overall grade to this team's Presentation skills?"].dropna(),
        bins=10,
        edgecolor="black",
        color="skyblue",
    )
    plt.title("Histogram of Presentation Skills Grades", fontsize=12)
    plt.xlabel("Presentation Skills Grade", fontsize=10)
    plt.ylabel("Frequency", fontsize=10)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.grid(True, linestyle="--", alpha=0.7)

    plt.subplot(1, 3, 3)
    plt.hist(
        responses["Overall grade to this team's Research topic and (summary) paper content?"].dropna(),
        bins=10,
        edgecolor="black",
        color="skyblue",
    )
    plt.title("Histogram of Research Topic and Paper Content Grades", fontsize=12)
    plt.xlabel("Research Topic and Paper Content Grade", fontsize=10)
    plt.ylabel("Frequency", fontsize=10)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.grid(True, linestyle="--", alpha=0.7)

    plt.savefig(output_path)


def apply_iqr(data: pd.Series, return_outliers=True) -> pd.Series:
    """Identifies student outliers using the IQR method"""

    # Calculate Q1, Q3, IQR, lower and upper whiskers
    Q1 = data.quantile(0.25)  # 25th percentile
    Q3 = data.quantile(0.75)  # 75th percentile
    IQR = Q3 - Q1
    lower_whisker = Q1 - 1.5 * IQR
    upper_whisker = Q3 + 1.5 * IQR

    outliers = data[(data < lower_whisker) | (data > upper_whisker) | (data == 0)]
    filtered_data = data[(data >= lower_whisker) & (data <= upper_whisker) & (data != 0)]

    return filtered_data if not return_outliers else outliers


class Grader:
    SPREADSHEET_COLUMN_NAMES = {
        "email": "Email",
        "team_name": "Team_Name",
        "slide_deck": "Overall grade to this team's Slide deck?",
        "presentation_skills": "Overall grade to this team's Presentation skills?",
        "research_topic": "Overall grade to this team's Research topic and (summary) paper content?",
    }

    def __init__(
        self,
        course_id: int,
        module_title: str,
        api_token: Optional[str] = None,
    ):
        self.canvas = CanvasAPI(course_id=course_id, api_token=api_token)
        self.google = GoogleServicesManager()
        self.module_id_with_presentations = self.canvas.get_module_by_title(module_title)
        self.student_records: StudentRecords = []
        self.worksheet: Worksheet

    def set_worksheet(self, sheet_id: str, worksheet_index: int = 1):
        self.worksheet = self.google.open_spreadsheet_by_id(sheet_id).get_worksheet(worksheet_index)

    def read_worksheet(self) -> StudentRecords:
        self.student_records: StudentRecords = []
        worksheet_records = self.google.read_worksheet(self.worksheet)
        for record in worksheet_records:
            self.student_records.append(StudentRecord(**record))  # type: ignore
        return self.student_records

    def update_worksheet(self):
        self.google.update_worksheet_from_records(self.worksheet, self.student_records)  # type: ignore

    def convert_student_record_sheets_to_team_info(self, Team_Name: str) -> TeamInfo:
        # get the team that has the project_path
        team_record = [record for record in self.student_records if record["Team_Name"] == Team_Name]
        if not team_record:
            raise ValueError(f"Team info not found for team: {Team_Name}")

        team_name = team_record[0]["Team_Name"]
        topic = team_record[0]["Topic"]
        team_members: List[TeamMember] = []  # name and email
        for record in team_record:
            team_members.append(TeamMember(name=record["Names"], email=record["Email"]))

        return TeamInfo(
            team_name=team_name,
            topic=topic,
            team_members=team_members,
        )

    def convert_team_info_to_student_record(self, team_info: TeamInfo, Team_Name: str) -> StudentRecord:
        """TODO: Don't know if is necessary - Not fully implemented"""
        return StudentRecord(Team_Name=team_info.team_name, Topic=team_info.topic, **team_info.model_dump())

    def is_a_project_folder(self, path: str) -> bool:
        return (
            os.path.exists(path)
            and os.path.isdir(path)
            and "paper.pdf" in os.listdir(path)
            and ("presentation.pdf" in os.listdir(path) or "presentation.pptx" in os.listdir(path))
            and "github.txt" in os.listdir(path)
        )

    def get_folders_with_team(self, path: str) -> List[str]:
        # Get the folders that contain the team_info.yml file
        folders = []
        for root, dirs, files in os.walk(path):
            if self.is_a_project_folder(root):
                folders.append(root)
        # Print("folders = ", folders)
        return folders

    def set_module_id_with_presentations(self, module_title: str):
        self.module_id_with_presentations = self.canvas.get_module_by_title(module_title)

    def get_pages_to_create(self, folders: List[str]) -> List[str]:
        """Get a list of folders that do not have a Canvas pages in the presentations module.

        This method checks each folder against existing Canvas pages to determine which folders
        need new pages created. It uses the team name from the folder path to match against
        Canvas page titles.

        Args:
            folders: List of folder paths to check for existing Canvas pages.

        Returns:
            List[str]: List of folder paths that need Canvas pages created.

        Example:
            >>> grader = Grader(...)
            >>> folders = ['/path/to/team1', '/path/to/team2']
            >>> pages_to_create = grader.get_pages_to_create(folders)
            >>> print(pages_to_create)
            ['/path/to/team2']  # Only team2 needs a page created
        """
        # Get the pages in the module
        pages_created = self.canvas.list_module_items(self.module_id_with_presentations.id)
        Print("pages already created = ", pages_created)
        pages_to_create: List[str] = []
        for folder in folders:
            team_name = os.path.basename(folder)
            # Check if the page already exists
            page_exists = any([team_name == page.title for page in pages_created])
            if not page_exists:
                pages_to_create.append(folder)
        Print("pages to create = ", pages_to_create)
        return pages_to_create

    def get_assignment_id_by_title(self, assignment_title):
        assignment_id = self.canvas.get_assignment_by_title(assignment_title)
        if assignment_id is None:
            raise Exception("Can't find assignment id with assignment title.")
        return assignment_id

    def get_spreadsheet_by_id(self, spreadsheet_id: str):
        spreadsheet = self.google.open_spreadsheet_by_id(spreadsheet_id)
        if spreadsheet is None:
            raise Exception("Can't find spreadsheet with id")
        return spreadsheet

    def get_google_form_responses(self, form_id) -> pd.DataFrame:
        responses = self.google.get_form_responses(form_id)  # DataFrame
        if responses is None:
            raise ValueError("No responses found in Google Form.")
        return responses

    def load_data_from_spreadsheet(self, spreadsheet_file: str) -> pd.DataFrame:
        """Loads form responses using column names"""

        # Will need to adjust for actual column names
        columns_to_read = [
            self.SPREADSHEET_COLUMN_NAMES["email"],
            self.SPREADSHEET_COLUMN_NAMES["slide_deck"],
            self.SPREADSHEET_COLUMN_NAMES["presentation_skills"],
            self.SPREADSHEET_COLUMN_NAMES["research_topic"],
            self.SPREADSHEET_COLUMN_NAMES["team_name"],
        ]
        data = pd.read_excel(spreadsheet_file, usecols=columns_to_read)

        if data.empty:
            raise ValueError("Error: The file is empty or the columns do not match.")

        # Normalize email addresses to lowercase
        data[self.SPREADSHEET_COLUMN_NAMES["email"]] = data[self.SPREADSHEET_COLUMN_NAMES["email"]].str.lower()

        return data

    def calculate_group_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculates the average grade for each team on their slide deck, presentation skills, and research topic and paper content"""

        # Group by 'Team' and calculate average for each grade category
        group_avg = (
            data.groupby(self.SPREADSHEET_COLUMN_NAMES["team_name"])
            .agg(
                {
                    self.SPREADSHEET_COLUMN_NAMES["slide_deck"]: "mean",
                    self.SPREADSHEET_COLUMN_NAMES["presentation_skills"]: "mean",
                    self.SPREADSHEET_COLUMN_NAMES["research_topic"]: "mean",
                }
            )
            .reset_index()
        )

        group_avg.rename(
            columns={
                self.SPREADSHEET_COLUMN_NAMES["slide_deck"]: "Average Slide Deck Grade",
                self.SPREADSHEET_COLUMN_NAMES["presentation_skills"]: "Average Presentation Skills Grade",
                self.SPREADSHEET_COLUMN_NAMES["research_topic"]: "Average Research and Topic Grade",
            },
            inplace=True,
        )

        # Drop rows with any NaN values
        group_avg = group_avg.dropna()
        group_avg.reset_index(drop=True, inplace=True)

        return group_avg

    def calculate_student_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculates the averages students gave for each team based on each category"""
        student_avg = (
            data.groupby(self.SPREADSHEET_COLUMN_NAMES["email"])
            .agg(
                {
                    self.SPREADSHEET_COLUMN_NAMES["slide_deck"]: "mean",
                    self.SPREADSHEET_COLUMN_NAMES["presentation_skills"]: "mean",
                    self.SPREADSHEET_COLUMN_NAMES["research_topic"]: "mean",
                }
            )
            .reset_index()
        )

        student_avg.rename(
            columns={
                self.SPREADSHEET_COLUMN_NAMES["slide_deck"]: "Average grade given for Slide decks",
                self.SPREADSHEET_COLUMN_NAMES["presentation_skills"]: "Average grade given for Presentation skills",
                self.SPREADSHEET_COLUMN_NAMES[
                    "research_topic"
                ]: "Average grade given for Research topic and (summary) paper content",
            },
            inplace=True,
        )

        return student_avg

    def get_top_three_presentations(self, group_averages: pd.DataFrame) -> pd.DataFrame:
        # Calculate the overall average grade for each team
        group_averages["Overall Average Grade"] = group_averages[
            ["Average Slide Deck Grade", "Average Presentation Skills Grade", "Average Research and Topic Grade"]
        ].mean(axis=1)

        # Sort by the Overall Average Grade (descending order)
        top_3 = group_averages.sort_values(by="Overall Average Grade", ascending=False).head(3)

        return top_3

    def get_student_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Identifies students who provided outlier grades or zeros, and counts the number for each student."""

        outliers_count = {}  # Dictionary to store email and count of outliers/zeros

        for category in [
            self.SPREADSHEET_COLUMN_NAMES["slide_deck"],
            self.SPREADSHEET_COLUMN_NAMES["presentation_skills"],
            self.SPREADSHEET_COLUMN_NAMES["research_topic"],
        ]:
            # Identify outliers and zeros in the category
            outliers = apply_iqr(data[category])
            if not outliers.empty:
                # Get the emails of students who gave outliers or zeros
                emails = data.loc[outliers.index, "Email"]
                for email in emails:
                    if email in outliers_count:
                        outliers_count[email] += 1
                    else:
                        outliers_count[email] = 1

        # Convert the dictionary into a DataFrame for better readability
        outliers_df = pd.DataFrame(
            list(outliers_count.items()), columns=["Email", "Outlying Grades Given"]
        ).sort_values(by="Outlying Grades Given", ascending=False)

        return outliers_df

    def process_form_responses(self, spreadsheet_file: str):

        data = self.load_data_from_spreadsheet(spreadsheet_file)

        # Calculate each group average grades
        group_averages = self.calculate_group_averages(data)

        # Calculate student averages given for each team
        student_averages = self.calculate_student_averages(data)

        # Get the top 3 presentations
        top_3_presentations = self.get_top_three_presentations(group_averages)

        # Get student outliers
        student_outliers = self.get_student_outliers(data)

        return group_averages, student_averages, top_3_presentations, student_outliers

    def grade_presentation_project(
        self,
        form_id: str,
        assignment_title: str,
        emails: List[str],
        path_image: str,
    ):
        """Grade the presentation for a group of students, this will read the scores from a Google Forms and update the grades in Canvas"""
        Print("Grading presentation project...")
        # Get responses from Google Forms
        df_responses = self.google.get_form_responses(form_id)  # DataFrame
        if df_responses is None:
            raise Exception("No responses found in the Google Form.")
        excel_path = path_image.replace("png", "xlsx")
        df_responses.to_excel(excel_path)
        # fmt: off
        df_responses["Overall grade to this team's Slide deck?"] = pd.to_numeric(df_responses["Overall grade to this team's Slide deck?"], errors='coerce')
        df_responses["Overall grade to this team's Presentation skills?"] = pd.to_numeric(df_responses["Overall grade to this team's Presentation skills?"], errors='coerce')
        df_responses["Overall grade to this team's Research topic and (summary) paper content?"] = pd.to_numeric(df_responses["Overall grade to this team's Research topic and (summary) paper content?"], errors='coerce')
        # fmt: on
        Print("responses = ", df_responses["Email"])
        Print("\n\n")
        #### PROCESSING ####
        # processing - removing emails that are not in the class list
        students = self.canvas.get_users_in_course()
        student_emails = [student["email"].strip().lower() for student in students]
        Print("student_emails = ", student_emails)
        # Remove responses from students not in the class
        df_responses["Email"] = df_responses["Email"].str.strip().str.lower()
        df_responses = df_responses[df_responses["Email"].isin(student_emails)]
        Print("Cleaned responses = ", df_responses)
        # fmt: off
        # Check if there are repeated emails in the responses
        if df_responses["Email"].duplicated().any():
            Print("There are repeated emails in the responses")
            # Print the repeated emails
            Print(df_responses[df_responses["Email"].duplicated()])
            # Drop the repeated emails
            df_responses = df_responses.drop_duplicates(subset="Email")
        # TODO: Remove outliers
        create_image(df_responses, path_image)
        grade = (
            df_responses["Overall grade to this team's Slide deck?"].mean()
            + df_responses["Overall grade to this team's Presentation skills?"].mean()
            + df_responses["Overall grade to this team's Research topic and (summary) paper content?"].mean()
        ) / 3
        # fmt: on
        Print("Grade:", grade, log_type="INFO")

        # Get assignment id based on title
        assignment_id = self.get_assignment_id_by_title(assignment_title)

        # Update grades in Canvas
        emails = [email.strip().lower() for email in emails]
        for student in students:
            if student["email"].strip().lower() in emails:
                Print(f"Updating grade for {student['email']}", log_type="INFO")
                try:
                    self.canvas.update_student_grade(assignment_id, student["id"], grade)
                except Exception as e:
                    Print(f"Error updating grade for {student['email']}: {e}", log_type="ERROR")
        Print("Grading complete", log_type="INFO")

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

    def verify_project_files(self, folder_path: str) -> Tuple[str, List[str]]:
        """Verify all required project files exist and return the absolute folder path, team info, and any errors

        Args:
            folder_path (str): Path to the project folder

        Returns:
            Tuple[str, TeamInfo, List[str]]: Tuple containing (absolute_path, team_info, list_of_errors)
        """
        errors: List[str] = []
        # team_info: Union[TeamInfo, None] = None

        # Get absolute folder path
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        abs_folder_path = os.path.join(cur_dir, folder_path)
        abs_folder_path = os.path.abspath(abs_folder_path)

        if not os.path.exists(abs_folder_path):
            errors.append("Folder path does not exist")
            return abs_folder_path, errors

        # Check required files exist
        required_files = {
            "presentation.pdf": "Presentation file is missing",
            "paper.pdf": "Paper file is missing",
            "quiz.json": "Quiz file is missing",
            # "team_info.yml": "Team info file is missing",
            "github.txt": "Github file is missing",
        }

        for file, error_msg in required_files.items():
            file_path = os.path.join(abs_folder_path, file)
            if not os.path.exists(file_path):
                errors.append(error_msg)

        # # Try to load and verify team info if yml exists
        # team_info_path = os.path.join(abs_folder_path, "team_info.yml")
        # if os.path.exists(team_info_path):
        #     try:
        #         team_info = self.__read_team_info_file(team_info_path)
        #     except ValidationError as e:
        #         error_details = []
        #         for err in e.errors():
        #             field_path = " -> ".join(str(x) for x in err["loc"])
        #             error_details.append(f"\tField '{field_path}': {err['msg']}")
        #         errors.append(f"Invalid team_info.yml:\n" + "\n".join(error_details))
        #     except yaml.YAMLError as e:
        #         errors.append(f"Invalid YAML syntax in team_info.yml: {str(e)}")
        #     except Exception as e:
        #         errors.append(f"Unexpected error reading team_info.yml: {str(e)}")

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

        return abs_folder_path, errors

    def verify_all_projects(self, folders: List[str]) -> List[Tuple[str, List[str]]]:
        """Verify all projects in the given folders and return verification results for all folders.

        Args:
            folders (List[str]): List of folder paths to verify

        Returns:
            List[Tuple[str,  List[str]]]: List of tuples containing
                (folder_path, list_of_errors) for all folders
        """
        verification_results = []

        for folder in folders:
            result = self.verify_project_files(folder)
            verification_results.append(result)

        return verification_results

    def create_canvas_page_based_on_folder(self, folder_path: str) -> PageSchema:
        """
        Creates a Canvas page for a team project based on the contents of a folder.

        This function takes a folder path containing project materials (presentation, paper, team info),
        verifies all required files are present, and creates a formatted Canvas page with the team's
        information and uploaded materials.

        Args:
            folder_path (str): Path to the folder containing the team's project materials.
                             Must contain:
                             - presentation.pdf
                             - paper.pdf
                             - quiz.json
                             - github.txt
        Returns:
            PageSchema: The created Canvas page object containing the team's information and materials.

        Raises:
            ValueError: If any required files are missing or invalid, or if team_info cannot be parsed.

        Example:
            >>> grader = Grader(course_id=12345, module_title="Team Presentations")
            >>> page = grader.create_canvas_page_based_on_folder("path/to/team1_folder")
        """
        # Verify project files and get absolute path
        folder_path, errors = self.verify_project_files(folder_path)
        if errors:
            raise ValueError(f"Project verification failed:\n" + "\n".join(f"- {error}" for error in errors))
        team_name = os.path.basename(folder_path)
        team_info = self.convert_student_record_sheets_to_team_info(team_name)

        # Upload the presentation and paper
        presentation_url = self.canvas.upload_file(folder_path + "/presentation.pdf")
        paper_url = self.canvas.upload_file(folder_path + "/paper.pdf")
        github_url = self.canvas.upload_file(folder_path + "/github.txt")
        # Create a Canvas page
        team_members_html = "".join([f"<li>{member.name} - {member.email} </li>" for member in team_info.team_members])

        body = f"""
                <h2 style="color: #2c3e50;">Team Information</h2>
                <p><strong>Team Name:</strong> {team_info.team_name}</p>
                <p><strong>Topic:</strong> {team_info.topic}</p>
                <p><strong>Team Members:</strong></p>
                <ul style="list-style-type: disc; padding-left: 20px;">
                    {team_members_html}
                </ul>
                <p><strong>Github Repo:</strong> <a href="{github_url}" style="color: #3498db;">github</a></p>
                <p><strong>Presentation:</strong> <a href="{presentation_url}" style="color: #3498db;">presentation</a></p>
                <p><strong>Paper:</strong> <a href="{paper_url}" style="color: #3498db;">paper</a></p>
        """
        page = self.canvas.create_page(title=team_info.team_name, body=body)

        # Add the page to the module
        self.canvas.create_module_item(
            title=team_info.team_name,
            module_id=self.module_id_with_presentations.id,
            type="Page",
            page_url=page.url,
        )

        return page

    def retrieve_page_structure(self, url: str) -> PageSchema:
        return self.canvas.get_page_by_id(url)

    def add_google_forms_and_create_quiz(self, page: PageSchema, folder_path: str):
        page_status = self.get_page_status(page)
        if page.body and (page_status == "Quiz and Feedback added" or page_status == "Done"):
            Print("Form and quiz URLs already present on the page. Skipping update.")
            return None, None

        cur_dir = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.join(cur_dir, folder_path)
        folder_path = os.path.abspath(folder_path)
        assert os.path.exists(folder_path), "Folder path does not exist"
        quiz_path = folder_path + "/quiz.json"
        assert os.path.exists(quiz_path), "Quiz file does not exist"
        # Verify that schema for quiz is good
        team_name = os.path.basename(folder_path)

        # Create a create a google forms for feedback to open at start time and close at end time + 20minutes
        form = self.google.make_copy_of_form(
            "1XykFAgYiZgMLGq7qZTlVwwacGaA_hhMDsNqAN43M8IU",  # TODO: Need to create a shared form for everyone
            f"Feedback for {team_name}",
            True,
        )

        form_url = form["responderUri"]
        quiz = self.canvas.create_quiz_from_file(folder_path + "/quiz.json")
        quiz_url = quiz["html_url"]

        # Check if form and quiz already exist on the page to avoid duplicates
        old_body = page.body
        # Add the google form to the page
        body = f"""
            {old_body}
            <p><strong>Feedback Form:</strong> <a href="{form_url}" style="color: #3498db;">Feedback Form</a></p>
            <p><strong>Quiz:</strong> <a href="{quiz_url}" style="color: #3498db;">Quiz</a></p>
        """

        # create canvas quiz based on the quiz file
        return self.canvas.update_page(page.page_id, body=body), form

    def get_page_status(
        self, page: PageSchema
    ) -> Literal["Created", "Quiz and Feedback added", "Done", "Evaluation Form"]:
        if page.url is None:
            raise ValueError("Page ID is None")

        page = self.canvas.get_page_by_id(page.url)

        if not page.body:
            raise ValueError("Page body is None")

        if "Feedback Form:" in page.body:
            return "Quiz and Feedback added"
        elif "Evaluation Form" in page.body:
            return "Evaluation Form"
        elif "<img" in page.body:
            return "Done"
        # else
        return "Created"

    def remove_feedback_url_and_quiz(self, page: PageSchema):
        old_body: str = page.body  # type: ignore
        # Remove the feedback form and quiz
        if "Feedback Form:" in old_body:
            body = old_body.split("<p><strong>Feedback Form:</strong>")[0]
        else:  # It will not remove the feedback form
            body = old_body
        return self.canvas.update_page(page.page_id, body=body)

    def add_images_to_body(self, page: PageSchema, image_paths: List[str]):
        old_body: str = page.body  # type: ignore
        # Add the images to the body
        for image_path in image_paths:
            file_name = os.path.basename(image_path)
            image_url = self.canvas.upload_file(image_path)
            if file_name in old_body:  # Replace the image
                Print("*****")
                old_image_url = old_body.split(file_name)[0]
                old_image_url = old_image_url.split('src="')[-1]
                Print(f"old_image_url = {old_image_url}")
                old_body = old_body.replace(old_image_url, image_url)
            else:  # add image
                old_body += f'<img src="{image_url}" alt="Image" >'
            # add HTML comment to the body "DONE"
        return self.canvas.update_page(page.page_id, body=old_body)

    def get_pages_posted_in_module(self) -> List[PageSchema]:
        return self.canvas.get_module_pages(self.module_id_with_presentations.id)


if __name__ == "__main__":
    # Sample Implementation
    grader = Grader(course_id=15319, module_title="Fall 2024 - Presentation")
    grader.set_worksheet("1tuuIobh2R4KQJBxCPR60E0EFVW_jr9_l6Aaj3lx6qaQ", 0)
    # pprint.pprint(grader.worksheet.get_values())
    student_records = grader.read_worksheet()
    pprint.pprint(student_records)
    team_info = grader.convert_student_record_sheets_to_team_info("SampleTeam")
    print("\n\n******  team info ****** ")
    print(team_info)
