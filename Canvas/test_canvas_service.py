import json
import os
import unittest
from CanvasService import CanvasAPI

import sys

# Ensure the Canvas directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "Canvas")))


class TestCanvasAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up Canvas API with real course data
        cls.api_token = os.getenv("API_TOKEN")
        cls.course_id = 15319
        cls.assignment_id = 53371
        cls.user_id = 140799
        cls.canvas = CanvasAPI(course_id=cls.course_id)

    def test_get_student_grade(self):
        # Call the method
        current_grade = self.canvas.get_student_grade(self.assignment_id, self.user_id)

        # Assertions
        self.assertIsNotNone(current_grade, "Grade should not be None")
        print(f"Current grade for user {self.user_id}: {current_grade}")

    def test_update_student_grade(self):
        # Call the method to update grade
        new_grade = 10
        updated_grade = self.canvas.update_student_grade(
            self.assignment_id, self.user_id, new_grade
        )

        # Assertions
        self.assertEqual(
            str(updated_grade),
            str(new_grade),
            "Updated grade should match the new grade",
        )
        print(f"Updated grade for user {self.user_id}: {updated_grade}")

    def test_get_users_in_course(self):
        # Call the method to retrieve users
        users = self.canvas.get_users_in_course()

        # Assertions
        self.assertGreater(len(users), 0, "Users should be retrieved from the course")
        print("Users in course:")
        for user in users:
            print(f"Name: {user.get('name')}, Email: {user.get('email')}")

    def test_create_announcement(self):
        # Call the method to create an announcement
        announcement_title = "Test Announcement"
        announcement_message = "This is a test announcement. Please ignore."
        announcement = self.canvas.create_announcement(
            announcement_title, announcement_message
        )
        print(f"Announcement '{announcement['title']}' created successfully.")

    def test_create_quiz_and_add_question(self):
        # Call the method to create a quiz
        quiz_title = "Test Quiz (python method)"
        quiz_description = "This is a test quiz created via API"
        quiz_type = "assignment"
        time_limit = 30  # in minutes
        quiz = self.canvas._create_quiz(
            quiz_title, quiz_description, quiz_type, time_limit
        )
        quiz_id = quiz["id"]
        print(f"Quiz '{quiz['title']}' created successfully with ID {quiz['id']}.")

        # Add a quiz question
        question_data = {
            "question": {
                "question_name": "Test question",
                "question_text": "1 + 1 = ?",
                "question_type": "multiple_choice_question",
                "points_possible": 5,
                "answers": [
                    {"answer_text": "2", "answer_weight": 100},
                    {"answer_text": "1", "answer_weight": 0},
                    {"answer_text": "3", "answer_weight": 0},
                    {"answer_text": "4", "answer_weight": 0},
                ],
            }
        }
        question = self.canvas._add_question_to_quiz(quiz_id, question_data)
        assert question
        # Assertions
        self.assertIsNotNone(
            question, "Question should be added to the quiz successfully"
        )
        print(f"Question added successfully with ID {question['id']}")

    def test_create_quiz_from_file(self):
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to the quiz file
        quiz_file_path = os.path.join(current_dir, "canvas_quiz.json")

        # Read the expected content from the file
        with open(quiz_file_path, "r") as tmp_file:
            quiz_data = json.load(tmp_file)

        # Call the method to create quiz from file
        try:
            quiz_response = self.canvas.create_quiz_from_file(quiz_file_path)
            self.assertIsNotNone(
                quiz_response, "Quiz should be created successfully from file."
            )
            self.assertEqual(
                quiz_response["title"], quiz_data["title"], "Quiz title mismatch."
            )
            print("Quiz created successfully from file")
        finally:
            # Clean up the temporary file
            # os.remove(tmp_file_path)
            pass

    def test_upload_file(self):
        """testing the upload file method"""
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to the file
        file_path = os.path.join(current_dir, "../histogram.png")

        # Call the method to upload the file
        upload_response = self.canvas.upload_file(file_path)

        # Assertions
        self.assertIsNotNone(upload_response, "File should be uploaded successfully")
        print("response = ", upload_response)


if __name__ == "__main__":
    unittest.main()
