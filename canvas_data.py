import os
import requests

# Get user api token from .env file
CANVAS_API_TOKEN = os.getenv("API_TOKEN")

# URL, course ID, test user ID, and assignment ID of Sandbox Course (subject to change)
CANVAS_API_URL = "https://csulb.instructure.com"
COURSE_ID = 15319
TEST_USER_ID = 140799
ASSIGNMENT_ID = 53371

# Get Users from course
# Canvas API Documentation: https://canvas.instructure.com/doc/api/all_resources.html#method.courses.users
def get_users_in_course(course_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/users"
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}

    # Optional request params
    params = {"sort": "email", "enrollment_state": "active"}

    users = []
    while True:
        # Make API request
        response = requests.get(url, headers=headers, params=params)
        try:
            response.raise_for_status()  # Raises an exception for 4xx/5xx errors

            # Process response into json format
            data = response.json()
            users.extend(data)
            return users
        except requests.HTTPError as http_err:
            print(
                f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}"
            )
            break
        except requests.RequestException as req_err:
            print(f"An error occurred: {req_err}")
            break
    return users

# TODO: Possibly find student id from name and/or assignment id from name

# Get user's grade for assignment
def get_student_grade(course_id, assignment_id, user_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    headers = {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        submission = response.json()

        # Get current grade or return default value of 'Not graded'
        current_grade = submission.get('grade', 'Not graded')
        return current_grade
    except requests.HTTPError as http_err:
        print(
            f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}"
        )
    except requests.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    return None

# Update user's grade for assignment
def update_student_grade(course_id, assignment_id, user_id, new_grade):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    headers = {
        "Authorization": f"Bearer {CANVAS_API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "submission": {
            "posted_grade": new_grade
        }
    }

    try: 
        response = requests.put(url, headers=headers, json=data) 
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        updated_submission = response.json()
        updated_grade = updated_submission.get('grade', 'No grade available')
        return updated_grade
    except requests.HTTPError as http_err:
        print(
            f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}"
        )
    except requests.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    return None

# Post Announcements 
def create_announcement(course_id, title, message): 
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/discussion_topics"
    headers = {
        "Authorization": f"Bearer {CANVAS_API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "title": title,
        "message": message,
        "published": True, # If false, this message is in a draft state
        "is_announcement": True # If false, this message will appear in the discussion section instead
    }

    try: 
        response = requests.post(url, headers=headers, json=data) 
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        return response.json()
    except requests.HTTPError as http_err:
        print(
            f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}"
        )
    except requests.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    return None

# Create quiz
def create_quiz(course_id, title, description, quiz_type, time_limit, shuffle_answer=False):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/quizzes"
    headers = {
        "Authorization": f"Bearer {CANVAS_API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "quiz": {
            "title": title,
            "description": description,
            "quiz_type": quiz_type,
            "time_limit": time_limit,
            "shuffle_answers": shuffle_answer,
            "allowed_attempts": 1
        }
        # Quiz request parameters to potentially add: due_at, lock_at, unlock_at
    }

    try: 
        response = requests.post(url, headers=headers, json=data) 
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        return response.json()
    except requests.HTTPError as http_err:
        print(
            f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}"
        )
        print(f"Response context: {response.text}")
    except requests.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    return None

# Add question to quiz
def add_question_to_quiz(course_id, quiz_id, question_data):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions"
    print(url)
    headers = {
        "Authorization": f"Bearer {CANVAS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    try: 
        response = requests.post(url, headers=headers, json=question_data) 
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        return response.json()
    except requests.HTTPError as http_err:
        print(
            f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}"
        )
        print(f"Response context: {response.text}")
    except requests.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    return None


if __name__ == "__main__":
    # # Get current grade for test student
    # current_grade = get_student_grade(COURSE_ID, ASSIGNMENT_ID, TEST_USER_ID)
    # print(current_grade)

    # # Update grade for test student
    # new_grade = 10
    # updated_grade = update_student_grade(COURSE_ID, ASSIGNMENT_ID, TEST_USER_ID, new_grade)
    # print(updated_grade)

    # # Retrieve users
    # users = get_users_in_course(COURSE_ID)
    # if users:
    #     print("Users in the course:")
    #     for user in users:
    #         print(f"Name: {user['name']}, Email: {user['email']}")
    # else:
    #     print("No users found or unable to fetch users.")

    # # Create announcement 
    # announcement_title = "Test Announcement"
    # announcement_message = "This is a test announcement. Please ignore."
    # announcement = create_announcement(COURSE_ID, announcement_title, announcement_message)
    # if announcement:
    #     print(f"Announcement '{announcement['title']}' created successfully.")
    # else:
    #     print("Failed to create announcement.")

    # Create quiz
    quiz_title = "Test quiz"
    quiz_description = "This is a test quiz created via API"
    quiz_type = "assignment"
    time_limit = 30 # in minutes
    quiz = create_quiz(COURSE_ID, quiz_title, quiz_description, quiz_type, time_limit)
    if quiz:
        quiz_id = quiz['id']
        print(f"Quiz '{quiz['title']}' created successfully with ID {quiz_id}.")
    else:
        print(f"Failed to create quiz")

    # Add quiz question
    # Sample question (need a way to parse question into format below)
    # https://canvas.instructure.com/doc/api/quiz_questions.html#QuizQuestion
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
                    {"answer_text": "4", "answer_weight": 0}
                ]
        }
    }
    question = add_question_to_quiz(COURSE_ID, quiz_id, question_data)
    if question:
        print(f"Question added successfully with ID {question['id']}")
    else:
        print("Failed to add question")
