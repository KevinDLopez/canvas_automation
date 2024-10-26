import os
import pprint
from typing import List

import pandas as pd
import yaml
from Canvas.CanvasService import CanvasAPI
from Canvas.schemas import PageSchema
from GoogleServices.GoogleServices import GoogleServicesManager
from schemas import *


class Grader:
    def __init__(self, course_id: int):
        self.canvas = CanvasAPI(course_id=course_id)
        self.google = GoogleServicesManager()

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

    def __read_team_info_file(self, path: str) -> TeamInfo:
        assert path.endswith(".yml"), "File must be a YAML file"
        # Read the file
        # Parse the file
        with open(path, "r") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        # Validate the data
        team_info = TeamInfo(**data)
        return team_info

    def create_canvas_page_based_on_folder(self, folder_path: str):
        # Upload the presentation, paper, create quiz(not posted)
        # Create a Canvas page with the additions the links for the presentation, paper, github repo ( team_info.yml )

        # check that paths exist
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.join(cur_dir, folder_path)
        folder_path = os.path.abspath(folder_path)
        assert os.path.exists(folder_path), "Folder path does not exist"

        presentation_path = folder_path + "/presentation.pdf"
        paper_path = folder_path + "/paper.pdf"
        quiz_path = folder_path + "/quiz.json"
        team_info_path = folder_path + "/team_info.yml"
        assert os.path.exists(quiz_path), "Quiz file does not exist"
        assert os.path.exists(presentation_path), "Presentation file does not exist"
        assert os.path.exists(paper_path), "Paper file does not exist"
        assert os.path.exists(team_info_path), "Team info file does not exist"

        # Verify that schema for quiz is good
        team_info = self.__read_team_info_file(team_info_path)

        # Upload the presentation and paper
        presentation_url = self.canvas.upload_file(presentation_path)
        paper_url = self.canvas.upload_file(paper_path)

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
        # print(pprint.pformat(team_info.model_dump()))

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
    # Set up the grader
    grader = Grader(course_id=15319)

    # canvas = CanvasAPI(course_id=15319)
    # Grade the presentation project
    # grader.grade_presentation_project(
    #     form_id="1UwS-2ntDwCXjQWsS0ADsZvDWzV0MMeo6I-mw5zcbVrw",
    #     assignment_id=53371,
    #     emails=[
    #         "Kevin.Lopezchavez01@student.csulb.edu",
    #         "Jerry.Wu01@student.csulb.edu",
    #     ],
    # )

    page = grader.create_canvas_page_based_on_folder("SampleTeam")
    page = grader.add_google_forms_and_create_quiz(page, "SampleTeam")

    input("Press Enter to continue...")
    page = grader.remove_feedback_url_and_quiz(page)
    page = grader.add_images_to_body(page, ["./histogram.png"])
    print(pprint.pformat(page.model_dump()))
