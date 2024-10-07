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
            # Checks if response was successful
            response.raise_for_status()  # raises an exception if the response is not successful

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
        response.raise_for_status()  # raises an exception if the response is not successful
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
        response.raise_for_status()  # raises an exception if the response is not successful
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

# Get current grade for test student
current_grade = get_student_grade(COURSE_ID, ASSIGNMENT_ID, TEST_USER_ID)
print(current_grade)

# Update grade for test student
new_grade = 10
updated_grade = update_student_grade(COURSE_ID, ASSIGNMENT_ID, TEST_USER_ID, new_grade)
print(updated_grade)

# # Retrieve users
# users = get_users_in_course(COURSE_ID)

# if users:
#     print("Users in the course:")
#     for user in users:
#         print(f"Name: {user['name']}, Email: {user['email']}")
# else:
#     print("No users found or unable to fetch users.")