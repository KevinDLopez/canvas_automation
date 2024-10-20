from typing import List

import pandas as pd
from Canvas.CanvasService import CanvasAPI
from GoogleServices.GoogleServices import GoogleServicesManager


class Grader:
    def __init__(self, course_id: int):
        self.canvas = CanvasAPI(course_id=course_id)
        self.google = GoogleServicesManager()

    def grade_presentation_project(
        self, form_id: str, assignment_id: int, emails: List[str]
    ):
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

    def create_canvas_material_based_on_folder(self, folder_path: str):
        """Create a Canvas material based on the contents of a folder.
        Tt should look inside a folder for presentation, paper, and quiz(optional) and create a canvas page based on it
        """

        print("Creating Canvas material based on folder...")
        # Get files in folder
        # Create assignment in Canvas
        print("Material created")


if __name__ == "__main__":
    # Set up the grader
    grader = Grader(course_id=15319)

    # canvas = CanvasAPI(course_id=15319)
    # Grade the presentation project
    grader.grade_presentation_project(
        form_id="1UwS-2ntDwCXjQWsS0ADsZvDWzV0MMeo6I-mw5zcbVrw",
        assignment_id=53371,
        emails=[
            "Kevin.Lopezchavez01@student.csulb.edu",
            "Jerry.Wu01@student.csulb.edu",
        ],
    )
