import json
import os
import pprint
import unittest
from Canvas.CanvasService import CanvasAPI

import sys
import shutil

from Logging import Print

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
        updated_grade = self.canvas.update_student_grade(self.assignment_id, self.user_id, new_grade)

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
        announcement = self.canvas.create_announcement(announcement_title, announcement_message)
        print(f"Announcement '{announcement['title']}' created successfully.")

    def test_create_quiz_and_add_question(self):
        # Call the method to create a quiz
        quiz_title = "Test Quiz (python method)"
        quiz_description = "This is a test quiz created via API"
        quiz_type = "assignment"
        time_limit = 30  # in minutes
        quiz = self.canvas._create_quiz(quiz_title, quiz_description, quiz_type, time_limit)
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
        self.assertIsNotNone(question, "Question should be added to the quiz successfully")
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
            self.assertIsNotNone(quiz_response, "Quiz should be created successfully from file.")
            self.assertEqual(quiz_response["title"], quiz_data["title"], "Quiz title mismatch.")
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

    def test_create_module(self):
        """testing the create module method"""
        new_create_module = self.canvas.create_module(name="New Module")
        self.assertIsNotNone(new_create_module, "New module should be created successfully")
        print("new_module = ", new_create_module)

    def test_list_modules(self):
        """testing the list modules method"""
        modules = self.canvas.list_modules()
        self.assertGreater(len(modules), 0, "Modules should be listed successfully")

    def test_create_module_item(self):
        """testing the create module item method"""
        modules = self.canvas.list_modules()
        module_id = modules[0].id
        page = self.canvas.create_page(title="New Page", body="This is a new page")
        new_item = self.canvas.create_module_item(title="New Page", module_id=module_id, page_url=page.url)
        self.assertIsNotNone(new_item, "New module item should be created successfully")
        print("new_item = ", new_item)

    def test_list_module_items(self):
        """testing the list module items method"""
        modules = self.canvas.list_modules()
        module_id = modules[0].id
        items = self.canvas.list_module_items(module_id)
        self.assertGreater(len(items), 0, "Module items should be listed successfully")
        print("items = ", pprint.pformat([item.model_dump() for item in items]))

    def test_create_page(self):
        """testing the create page method"""
        page = self.canvas.create_page(title="New Page", body="This is a new page")
        self.assertIsNotNone(page, "Page should be created successfully")
        print("page = ", pprint.pformat(page.model_dump()))

    def test_list_pages(self):
        """testing the list pages method"""
        list_pages = self.canvas.list_pages()
        self.assertGreater(len(list_pages), 0, "Pages should be listed successfully")
        print("**list_pages = ", pprint.pformat([page.model_dump() for page in list_pages]), "\n\n")

    def test_update_page(self):
        """testing the update page method"""
        page = self.canvas.create_page(title="New Page", body="This is a new page")
        updated_page = self.canvas.update_page(id=page.page_id, body="This is an updated page")
        self.assertIsNotNone(updated_page, "Page should be updated successfully")
        print("updated_page = ", updated_page)

    def test_get_submissions(self):
        """Testing get_submissions method"""
        # Get submissions for a specific assignment
        submissions = self.canvas.get_submissions(1192803)

        # Assertions
        self.assertIsNotNone(submissions, "Submissions should not be None")
        self.assertIsInstance(submissions, list, "Submissions should be a list")
        print(f"Retrieved {len(submissions)} submissions for assignment {1192803}")

    def test_download_submission_attachments(self):
        """Testing download_all_submission_attachments method"""
        # Download submission attachments
        downloads = self.canvas.download_all_submission_attachments(1192803)

        # Assertions
        self.assertIsNotNone(downloads, "Download path should not be None")
        for submission_download_path in downloads:
            self.assertTrue(os.path.exists(submission_download_path), "Submission directory should exist")

        print(f"Downloaded submissions to {downloads}")

        # Cleanup downloaded files
        if downloads:
            parent_dir = os.path.dirname(downloads[0])
            Print("parent_dir = ", parent_dir, log_type="INFO")
            if os.path.exists(parent_dir):
                shutil.rmtree(parent_dir)


if __name__ == "__main__":
    unittest.main()
