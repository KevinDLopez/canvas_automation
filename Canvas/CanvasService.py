import os
import time
from typing import Any, Dict, List, Literal, Optional
import requests
import unittest
import json

from schemas import *


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
            endpoint = self.__get_next_page(response)
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

    def _create_quiz(
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

    def _add_question_to_quiz(self, quiz_id: int, question_data: Dict) -> Dict:
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

    def __get_next_page(self, response: requests.Response) -> Optional[str]:
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

    def _create_quiz_with_questions(self, validated_quiz: QuizSchema) -> Dict:
        """
        Create a quiz and add multiple questions based on the provided data.

        Args:
            validated_quiz (QuizSchema): An instance of QuizSchema containing the quiz information and questions.

        Returns:
            Dict: The created quiz data.

        Raises:
            ValidationError: If the input data does not conform to the schema.
            requests.HTTPError: If the quiz creation or question addition fails after retries.
            ValueError: If the quiz ID is not found after creation.
        """
        # Step 1: Create the quiz
        quiz = self._create_quiz(
            title=validated_quiz.title,
            description=validated_quiz.description,
            quiz_type=validated_quiz.quiz_type,
            time_limit=validated_quiz.time_limit,
            shuffle_answers=validated_quiz.shuffle_answers,
            allowed_attempts=validated_quiz.allowed_attempts,
        )
        # Step 2: Add questions to the quiz
        for idx, question in enumerate(validated_quiz.questions, start=1):
            question_dict = question.model_dump()
            question_data = {"question": question_dict}
            added_question = self._add_question_to_quiz(quiz["id"], question_data)
            if not added_question:
                raise requests.HTTPError(
                    f"Failed to add question '{question.question_name}' to the quiz."
                )

        print(
            f"Quiz '{validated_quiz.title}' created successfully with all questions added."
        )
        return quiz

    def create_quiz_from_file(self, file_path: str) -> Dict:
        """
        Create a quiz by reading quiz data from a JSON file.

        Args:
            file_path (str): Path to the JSON file containing quiz data.

        Returns:
            Dict: The created quiz data.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file content cannot be parsed as JSON.
            ValidationError: If the file content does not conform to the QuizSchema.
            requests.HTTPError: If the quiz creation or question addition fails after retries.
        """

        # Step 1: Check if the file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")

        # Step 2: Read and parse the JSON file
        try:
            with open(file_path, "r") as f:
                quiz_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON file: {e}")

        # Unpacking the JSON data into the schema, would raise errors if the data is invalid
        validated_quiz = QuizSchema(**quiz_data)

        # Step 3: Validate and create the quiz with questions
        return self._create_quiz_with_questions(validated_quiz)
