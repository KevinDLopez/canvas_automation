import os
import time
from typing import Any, Dict, List, Literal, Optional
import requests
import unittest


class CanvasAPI:
    def __init__(
        self,
        course_id: int,
        api_token: Optional[str] = None,
        base_url: str = "https://csulb.instructure.com",
    ):
        """
        Initialize the CanvasAPI instance.

        Args:
            course_id (int): The ID of the course.
            api_token (str, optional): Canvas API token. If not provided, it will
                                       attempt to read from the 'API_TOKEN' environment variable.
            base_url (str): Base URL for the Canvas instance.
        """
        self.course_id = course_id
        self.api_token = api_token or os.getenv("API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "API token must be provided either as an argument or via the 'API_TOKEN' environment variable."
            )

        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, method: Literal["GET", "PUT", "POST"], endpoint: str, **kwargs
    ) -> dict:
        """
        Helper method to make HTTP requests and handle errors consistently.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST', 'PUT').
            endpoint (str): The endpoint part of the URL after /courses/{course_id}.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            Optional[Any]: The parsed JSON response if successful, otherwise None.
        """
        url = f"{self.base_url}/api/v1/courses/{self.course_id}/{endpoint}"
        attempts = 3
        for attempt in range(attempts):
            try:
                response = requests.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as http_err:
                print(
                    f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}"
                )
                print(f"Retrying in 1 second (attempt {attempt + 1}/{attempts})...")
                time.sleep(1)  # Wait for 1 second before retrying
        raise requests.HTTPError(f"Failed to make request after {attempts} attempts")

    def get_users_in_course(self) -> List[Dict]:
        """
        Retrieve active users enrolled in the course.

        Returns:
            List[Dict]: A list of user dictionaries.
        """
        params = {"sort": "email", "enrollment_state": "active"}
        users = []
        endpoint = "users"

        while endpoint:
            response = requests.get(
                f"{self.base_url}/api/v1/courses/{self.course_id}/{endpoint}",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()  # Ensure we handle any errors
            data = response.json()
            users.extend(data)
            # Handle pagination
            endpoint = self._get_next_page(response)
            params = {}  # Clear params after the first request
        return users

    def get_student_grade(self, assignment_id: int, user_id: int) -> str:
        """
        Retrieve a student's grade for a specific assignment.

        Args:
            assignment_id (int): The ID of the assignment.
            user_id (int): The ID of the user.

        Returns:
            Optional[str]: The grade if available, otherwise None.
        """
        endpoint = f"assignments/{assignment_id}/submissions/{user_id}"
        submission = self._make_request("GET", endpoint)
        return submission.get("grade", "Not graded")

    def update_student_grade(
        self, assignment_id: int, user_id: int, new_grade: float
    ) -> str:
        """
        Update a student's grade for a specific assignment.

        Args:
            assignment_id (int): The ID of the assignment.
            user_id (int): The ID of the user.
            new_grade (float): The new grade to assign.

        Returns:
            str: The updated grade if successful, otherwise None.
        """
        endpoint = f"assignments/{assignment_id}/submissions/{user_id}"
        data = {"submission": {"posted_grade": new_grade}}
        updated_submission = self._make_request("PUT", endpoint, json=data)
        return updated_submission.get("grade", "No grade available")

    def create_announcement(self, title: str, message: str) -> Dict:
        """
        Create an announcement in the course.

        Args:
            title (str): The title of the announcement.
            message (str): The message content of the announcement.

        Returns:
            Optional[Dict]: The created announcement data if successful, otherwise None.
        """
        endpoint = "discussion_topics"
        data = {
            "title": title,
            "message": message,
            "published": True,  # If False, the message is in a draft state
            "is_announcement": True,  # If False, the message appears in the discussion section
        }
        return self._make_request("POST", endpoint, json=data)

    def create_quiz(
        self,
        title: str,
        description: str,
        quiz_type: str,
        time_limit: int,
        shuffle_answers: bool = False,
        allowed_attempts: int = 1,
    ) -> Dict:
        """
        Create a quiz in the course.

        Args:
            title (str): The title of the quiz.
            description (str): The description of the quiz.
            quiz_type (str): The type of the quiz (e.g., 'assignment').
            time_limit (int): Time limit for the quiz in minutes.
            shuffle_answers (bool, optional): Whether to shuffle answers. Defaults to False.
            allowed_attempts (int, optional): Number of allowed attempts. Defaults to 1.

        Returns:
            Dict: The created quiz data if successful, otherwise None.
        """
        endpoint = "quizzes"
        data = {
            "quiz": {
                "title": title,
                "description": description,
                "quiz_type": quiz_type,
                "time_limit": time_limit,
                "shuffle_answers": shuffle_answers,
                "allowed_attempts": allowed_attempts,
            }
        }
        return self._make_request("POST", endpoint, json=data)

    def add_question_to_quiz(self, quiz_id: int, question_data: Dict) -> Dict:
        """
        Add a question to a specific quiz.

        Args:
            quiz_id (int): The ID of the quiz.
            question_data (Dict): The question data as per Canvas API specifications.

        Returns:
            Dict: The added question data if successful, otherwise None.
        """
        endpoint = f"quizzes/{quiz_id}/questions"
        return self._make_request("POST", endpoint, json=question_data)

    def _get_next_page(self, response: requests.Response) -> Optional[str]:
        """
        Parse the 'Link' header to find the URL for the next page.

        Args:
            response (requests.Response): The response object.

        Returns:
            Optional[str]: The URL for the next page if available, otherwise None.
        """
        link_header = response.headers.get("Link", "")
        if link_header:
            links = link_header.split(",")
            for link in links:
                parts = link.split(";")
                if len(parts) == 2 and 'rel="next"' in parts[1]:
                    next_url = parts[0].strip().strip("<>").strip()
                    return next_url
        return None


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
        quiz_title = "Test Quiz"
        quiz_description = "This is a test quiz created via API"
        quiz_type = "assignment"
        time_limit = 30  # in minutes
        quiz = self.canvas.create_quiz(
            quiz_title, quiz_description, quiz_type, time_limit
        )
        if not quiz:
            raise Exception("Failed to create quiz")
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
        question = self.canvas.add_question_to_quiz(quiz_id, question_data)
        assert question
        # Assertions
        self.assertIsNotNone(
            question, "Question should be added to the quiz successfully"
        )
        print(f"Question added successfully with ID {question['id']}")


if __name__ == "__main__":
    unittest.main()
