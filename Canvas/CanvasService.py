import base64
import os
import time
from typing import Any, Dict, List, Literal, Optional
import requests
import unittest
import json

from Canvas.schemas import *
import pprint
from Logging import Print, set_log_level, LogLevel
from dotenv import load_dotenv


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

    def _make_request(self, method: Literal["GET", "PUT", "POST", "DELETE"], endpoint: str, **kwargs) -> dict:
        """
        Helper method to make HTTP requests and handle errors consistently.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
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
                Print(f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}", log_type="ERROR")
                Print(f"Response content: {response.content.decode('utf-8')}", log_type="ERROR")
                Print(f"Retrying in 1 second (attempt {attempt + 1}/{attempts})...", log_type="ERROR")
                time.sleep(1)  # Wait for 1 second before retrying
            except Exception as err:
                Print(f"Other error occurred: {err}", log_type="ERROR")

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

    def update_student_grade(self, assignment_id: int, user_id: int, new_grade: float) -> str:
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

    def get_submissions(self, assignment_id: int) -> List[SubmissionSchema]:
        """
        Retrieve all submissions for a specific assignment.

        Args:
            assignment_id (int): The ID of the assignment.

        Returns:
            List[Dict]: A list of submission dictionaries.
        """
        params = {"include[]": "attachments"}
        submissions = self._make_request("GET", f"assignments/{assignment_id}/submissions", params=params)
        return [SubmissionSchema(**submission) for submission in submissions]

    def download_all_submission_attachments(self, assignment_id: int, download_dir: Optional[str] = None) -> List[str]:
        """
        Download all submission files for a specific assignment.

        Args:
            assignment_id (int): The ID of the assignment.
            download_dir (str, optional): Directory to save files. Defaults to current directory.

        Returns:
            List[str]: List of paths to downloaded files.
        """
        download_dir = download_dir or os.getcwd()
        if not os.path.isdir(download_dir):
            raise ValueError(f"Invalid download directory: {download_dir}")

        downloaded_files = []
        for submission in self.get_submissions(assignment_id):
            if not submission.attachments:
                Print(f"No attachments found for submission {submission.user_id}", log_type="WARN")
                continue
            folder_path = os.path.join(download_dir, str(submission.user_id))
            os.makedirs(folder_path, exist_ok=True)
            for attachment in submission.attachments:
                file_url = attachment["url"]
                filename = attachment["filename"]
                filepath = os.path.join(folder_path, f"{filename}")
                response = requests.get(file_url, headers=self.headers)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(response.content)
                downloaded_files.append(filepath)
                Print(f"Downloaded {filename} to {filepath}", log_type="INFO")
        return downloaded_files

    def download_student_submission_attachments(
        self, assignment_id: int, user_id: int, download_dir: Optional[str] = None
    ) -> List[str]:
        """
        Download submission files for a specific student's assignment.

        Args:
            assignment_id (int): The ID of the assignment.
            student_id (int): The ID of the student.
            download_dir (str, optional): Directory to save files. Defaults to current directory.

        Returns:
            List[str]: List of paths to downloaded files.
        """
        if download_dir:
            os.makedirs(download_dir, exist_ok=True)
        else:
            download_dir = os.getcwd()

        downloaded_files = []
        for submission in self.get_submissions(assignment_id):
            if submission.user_id != user_id:
                Print(
                    f"skipping submission for student {user_id}, the submission belongs to {submission.user_id}",
                    log_type="INFO",
                )
                continue
            Print(f"found submission for student {user_id}", log_type="INFO")
            if not submission.attachments:
                Print(f"No attachments found for student {user_id}", log_type="WARN")
                return []

            for attachment in submission.attachments:
                file_url = attachment["url"]
                filename = attachment["filename"]
                filepath = os.path.join(download_dir, f"{filename}")
                response = requests.get(file_url, headers=self.headers)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(response.content)
                downloaded_files.append(filepath)
                Print(f"Downloaded {filename} to {filepath}", log_type="INFO")
            break

        return downloaded_files

    def get_student_id_by_email(self, email: str) -> Optional[int]:
        """
        Get the ID of a student by their email.
        """
        return 143898  # Temp while testign only
        users = self.get_users_in_course()
        Print(f"users = {users}", log_type="DEBUG")
        for user in users:
            if user["email"].strip().lower() == email.strip().lower():
                return user["id"]
        return None

    def get_assignments(self) -> List[AssignmentSchema]:
        """
        Retrieve all assignments in the course.

        Returns:
            List[AssignmentSchema]: A list of assignment dictionaries.
        """
        endpoint = "assignments"
        assignments_ = self._make_request("GET", endpoint)
        assignments: List[AssignmentSchema] = []
        for assignment in assignments_:
            assignments.append(AssignmentSchema(**assignment))
        return assignments

    def get_assignment_by_title(self, assignment_title) -> int:
        """
        Gets assignment id based on title

        Returns:
            Assignment ID if it exists
        """
        assignments = self.get_assignments()
        for assignment in assignments:
            if assignment.name.strip().lower() == assignment_title.strip().lower():
                return assignment.id
        raise ValueError(
            f"Assignment with title '{assignment_title}' not found. The assignments are {[a.name for a in assignments]}"
        )

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

    # __private
    # _protected
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
        quiz = self._create_quiz(  # TODO: Might need to change some of the parameters
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
                raise requests.HTTPError(f"Failed to add question '{question.question_name}' to the quiz.")

        Print(f"Quiz '{validated_quiz.title}' created successfully with all questions added.", log_type="INFO")
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

    def get_public_file_url(self, file_id: int) -> str:
        """
        Retrieve the public URL for a file in the course.

        Args:
            file_id (int): The ID of the file.

        Returns:
            str: The public URL for the file.
        """
        url = f"{self.base_url}/api/v1/files/{file_id}/public_url"
        response = requests.get(url, headers=self.headers).json()
        return response["public_url"]

        return response["url"]

    def upload_file(self, file_path: str) -> str:
        """
        Upload an image to the course's files.

        Args:
            file_path (str): The local path to the image file (e.g., '/path/to/image.png').

        Returns:
            str: public URL .

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a PNG file or if the file size cannot be determined.
            requests.HTTPError: If the upload fails.
        """
        # Step 1: Check if the file exists and is a .png file
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")
        # if not file_path.lower().endswith(".png"):
        #     raise ValueError("Only .png files are supported for this upload method.")
        file_path = os.path.abspath(file_path)
        Print(f"file_path = {file_path}")

        # Step 2: Get the file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("Cannot upload an empty file.")
        Print("File size = ", file_size)

        # Step 3: Initiate the file upload
        file_name = os.path.basename(file_path)
        Print("file_name = ", file_name)
        file_type = file_name.split(".")[-1]
        data = {
            "name": file_name,
            # "content_type": "image/png",
            "size": str(file_size),
            "parent_folder_path": "",  # Modify as needed for specific folder
            "on_duplicate": "rename",  # Rename the file if a file with the same name exists
            "Authorization": f"Bearer {self.api_token}",
        }

        # Using _make_request to initiate the file upload
        upload_info = self._make_request("POST", "files", json=data)

        # Step 2: Upload the file to the pre-signed URL
        upload_url = upload_info["upload_url"]
        upload_params = upload_info["upload_params"]

        with open(file_path, "rb") as file_data:
            files = {"file": (file_name, file_data)}
            upload_response = requests.post(upload_url, data=upload_params, files=files)
            try:
                upload_response.raise_for_status()
            except requests.HTTPError as e:
                Print(f"HTTPError during file upload: {e}")
                Print(f"Response Status Code: {upload_response.status_code}")
                Print(f"Response Text: {upload_response.text}")
                raise

        # Step 5: Confirm the file upload and retrieve
        if upload_response.status_code == 201:
            Print(f"File '{file_name}' uploaded successfully!")
            # The file URI is usually returned as part of the upload_info or can be constructed from the file details
            """
            Print("upload_info", pprint.pformat(upload_info))
            {
                "file_param": "file",
                "progress": None,
                "upload_params": {"content_type": "image/png", "filename": "histogram.png"},
                "upload_url": "https://inst-fs-pdx-prod.inscloudgate.net/files?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpYXQiOjE3Mjk4ODUxMTEsInVzZXJfaWQiOiIyMTEzOTAwMDAwMDAwMDU4MTMiLCJyZXNvdXJjZSI6Ii9maWxlcyIsImNhcHR1cmVfdXJsIjoiaHR0cHM6Ly9jc3VsYi5pbnN0cnVjdHVyZS5jb20vYXBpL3YxL2ZpbGVzL2NhcHR1cmUiLCJjYXB0dXJlX3BhcmFtcyI6eyJjb250ZXh0X3R5cGUiOiJDb3Vyc2UiLCJjb250ZXh0X2lkIjoiMjExMzkwMDAwMDAwMDE1MzE5IiwidXNlcl9pZCI6IjIxMTM5MDAwMDAwMDAwNTgxMyIsImZvbGRlcl9pZCI6IjIxMTM5MDAwMDAwMDA5NjIwMyIsInJvb3RfYWNjb3VudF9pZCI6IjIxMTM5MDAwMDAwMDAwMDAwMSIsInF1b3RhX2V4ZW1wdCI6ZmFsc2UsIm9uX2R1cGxpY2F0ZSI6InJlbmFtZSIsInByb2dyZXNzX2lkIjpudWxsLCJpbmNsdWRlIjpudWxsfSwibGVnYWN5X2FwaV9kZXZlbG9wZXJfa2V5X2lkIjoiMTcwMDAwMDAwMDAwMDE2IiwibGVnYWN5X2FwaV9yb290X2FjY291bnRfaWQiOiIyMTEzOTAwMDAwMDAwMDAwMDEiLCJleHAiOjE3Mjk4ODU3MTF9.BymDwnCLWTpRgo1wdRMGtOMbT1cDzxqTyYKJSdrO0pcQJf1n6g_h-3014MWKpzFmqV5zq49TGVsPbKKGgVQp-w",
            }


            Print("upload_reponse", pprint.pformat(upload_response.json()))
            {
                "category": "uncategorized",
                "content-type": "image/png",
                "created_at": "2024-10-25T19:38:31Z",
                "display_name": "histogram-4.png",
                "filename": "histogram.png",
                "folder_id": 96203,
                "hidden": False,
                "hidden_for_user": False,
                "id": 19085526,
                "instfs_uuid": "026c4bf1-408b-4a0a-8669-cc5124287114",
                "location": "https://csulb.instructure.com/api/v1/files/19085526?include%5B%5D=enhanced_preview_url",
                "lock_at": None,
                "locked": False,
                "locked_for_user": False,
                "media_entry_id": None,
                "mime_class": "image",
                "modified_at": "2024-10-25T19:38:31Z",
                "preview_url": "/courses/15319/files/19085526/file_preview?annotate=0&verifier=KyOBPQpIratVM9u5nL4hx7K9O2OjfW6sIEogYgac",
                "size": 23543,
                "thumbnail_url": "https://csulb.instructure.com/images/thumbnails/19085526/KyOBPQpIratVM9u5nL4hx7K9O2OjfW6sIEogYgac",
                "unlock_at": None,
                "updated_at": "2024-10-25T19:38:31Z",
                "upload_status": "success",
                "url": "https://csulb.instructure.com/files/19085526/download?download_frd=1&verifier=KyOBPQpIratVM9u5nL4hx7K9O2OjfW6sIEogYgac",
                "uuid": "KyOBPQpIratVM9u5nL4hx7K9O2OjfW6sIEogYgac",
                "visibility_level": "inherit",
            }
            """

            # self.get_public_file_url(upload_response.json()["id"]),
            return upload_response.json()["url"]
        else:
            raise requests.HTTPError(f"File upload failed with status: {upload_response.status_code}")

    def list_modules(self) -> List[ModuleSchema]:
        """
        Retrieve all modules in the course.

        Returns:
            List[Dict]: A list of module dictionaries.
        """
        endpoint = "modules"
        modules_dict = self._make_request("GET", endpoint)
        # Print(modules_dict[0])
        modules: List[ModuleSchema] = [ModuleSchema(**module) for module in modules_dict]
        return modules

    def get_module_by_title(self, name: str) -> ModuleSchema:
        """
        Retrieve a specific module by its ID.

        Args:
            name (str): The ID of the module.

        Returns:
            Dict: The module data if found, otherwise None.
        """
        self.list_modules()
        for module in self.list_modules():
            if module.name == name:
                return module
        raise ValueError(f"Module with name '{name}' not found.")

    def create_module(
        self, name: str, position: Optional[int] = None, unlock_at: Optional[datetime] = None
    ) -> ModuleSchema:
        """
        Create a module in the course.

        Args:
            name (str): The name of the module.
            position (int): The position of the module in the course.

        Returns:
            Dict: The created module data if successful, otherwise None.
        """
        endpoint = "modules"
        data = {"module": {"name": name}}
        if position:
            data["module"]["position"] = str(position)
        if unlock_at:
            data["module"]["unlock_at"] = unlock_at.isoformat()

        module = self._make_request("POST", endpoint, json=data)
        return ModuleSchema(**module)

    def list_module_items(self, module_id: int) -> List[ModuleItemSchema]:
        """
        Retrieve all items in a specific module.

        Args:
            module_id (int): The ID of the module.

        Returns:
            List[Dict]: A list of module item dictionaries.
        """
        endpoint = f"modules/{module_id}/items"
        moduleItem = self._make_request("GET", endpoint)
        return [ModuleItemSchema(**item) for item in moduleItem]

    def get_page_by_id(self, url: str) -> PageSchema:
        endpoint = f"pages/{url}"
        page = self._make_request("GET", endpoint)
        return PageSchema(**page)

    def get_module_pages(self, module_id: int) -> List[PageSchema]:
        items = self.list_module_items(module_id)
        pages: List[PageSchema] = []
        for item in items:
            if item.type == "Page":
                if not item.page_url:
                    raise ValueError(f"Page {item.id} has no page_url")
                pages.append(self.get_page_by_id(item.page_url))
        return pages

    def create_page(
        self,
        title: str,
        body: Optional[str] = None,
        editing_roles: Optional[Literal["teachers", "students", "members", "public"]] = None,
        notify_of_update: Optional[bool] = None,
        published: Optional[bool] = None,
        front_page: Optional[bool] = None,
        publish_at: Optional[datetime] = None,
    ) -> PageSchema:
        """
        Create a new wiki page with the specified parameters.

        :param title: The title for the new page.
        :param body: The content for the new page.
        :param editing_roles: Which user roles are allowed to edit this page.
                            Allowed values: 'teachers', 'students', 'members', 'public'.
        :param notify_of_update: Whether participants should be notified when this page changes.
        :param published: Whether the page is published (true) or draft state (false).
        :param front_page: Set an unhidden page as the front page (if true).
        :param publish_at: Schedule a future date/time to publish the page.
        """
        endpoint = "pages"
        data = {
            "wiki_page": {
                "title": title,
            }
        }
        if body:
            data["wiki_page"]["body"] = body
        if editing_roles:
            data["wiki_page"]["editing_roles"] = editing_roles
        if notify_of_update is not None:
            data["wiki_page"]["notify_of_update"] = str(notify_of_update)
        if published is not None:
            data["wiki_page"]["published"] = str(published)
        if front_page is not None:
            data["wiki_page"]["front_page"] = str(front_page)
        if publish_at:
            data["wiki_page"]["publish_at"] = publish_at.isoformat()

        page = self._make_request("POST", endpoint, json=data)
        Print("new_page = ")
        page = PageSchema(**page)
        pprint.pprint(page.model_dump()["body"])
        return page

    def update_page(self, id: int, body: str, title: Optional[str] = None) -> PageSchema:
        """
        Update an existing wiki page with the specified parameters.

        :param id: The ID of the page to update.
        :param body: The new content for the page.
        :param title: The new title for the page.
        """
        endpoint = f"pages/{id}"
        data = {
            "wiki_page": {
                "body": body,
            }
        }
        if title:
            data["wiki_page"]["title"] = title
        page = self._make_request("PUT", endpoint, json=data)
        return PageSchema(**page)

    def list_pages(self) -> List[PageSchema]:
        """
        Retrieve all pages in the course.

        Returns:
            List[Dict]: A list of page dictionaries.
        """
        endpoint = "pages"
        pages = self._make_request("GET", endpoint)
        return [PageSchema(**page) for page in pages]

    def create_module_item(
        self,
        title: str,
        module_id: int,
        page_url: str,
        type: Literal["File", "Page", "Discussion"] = "Page",
    ) -> ModuleItemSchema:
        """
        Create a module item in a specific module.

        Args:
            title (str): The title of the module item.
            module_id (str): The ID of the module.
            type (str): The type of the module item.

        Returns:
            Dict: The created module item data if successful, otherwise None.
        """
        endpoint = f"modules/{module_id}/items"
        data = {
            "module_item": {
                "title": title,
                "type": type,
                "page_url": page_url,
                # "content_id": 123,
            },
            # "Authorization": f"Bearer {self.api_token}",
        }
        module_item = self._make_request("POST", endpoint, json=data)
        return ModuleItemSchema(**module_item)


if __name__ == "__main__":
    set_log_level(LogLevel.DEBUG)
    if load_dotenv():
        api_token = os.getenv("API_TOKEN")
        print("API_TOKEN loaded successfully")
    else:
        raise ValueError("API_TOKEN not found in .env file")

    course_id = 15319
    canvas = CanvasAPI(course_id, api_token)
    assignment = canvas.get_submissions(1192803)  # It should at least not raise an error
    assignments = canvas.download_all_submission_attachments(
        1192803
    )  # IT should not raise an error, and it should download files in the cwd + /student_id folder

    raise Exception("stop here")
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = "../histogram.png"
    path = os.path.join(cur_dir, image_path)
    # Call the upload function
    url = canvas.upload_file(path)
    Print(f" URL for the uploaded file: {url}")

    modules = canvas.list_modules()
    a = modules[1].model_dump()

    # #  a new module
    newCreate_module = canvas.create_module(name="New Module")
    Print("new_module = ", newCreate_module)

    module_id = modules[0].id
    items = canvas.list_module_items(module_id)
    pages = canvas.get_module_pages(module_id)
    Print("**pages = ", pprint.pformat([page.model_dump() for page in pages]))
    raise Exception("stop here")
    Print("items = ", pprint.pformat([item.model_dump() for item in items]))

    page = canvas.create_page(
        title="New Page", body="This is a new page"
    )  # TODO: We need to add the body, add the files, link to github, etc
    Print("page = ", pprint.pformat(page.model_dump()))

    list_pages = canvas.list_pages()
    Print("**list_pages = ", pprint.pformat([page.model_dump() for page in list_pages]), "\n\n")

    updated_page = canvas.update_page(id=page.page_id, body="This is an updated page")
    Print("updated_page = ", updated_page)
    page.url
    # Create a new module item
    new_item = canvas.create_module_item(title="New Page", module_id=module_id, page_url=page.url)
    Print("new_item = ", new_item)
