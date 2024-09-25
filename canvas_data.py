import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get user api token from .env file
API_TOKEN = os.getenv("API_TOKEN")

# URL and course ID of Sandbox Course (subject to change)
CANVAS_API_URL = "https://csulb.instructure.com"
COURSE_ID = 15319

# Get Users from course
# Canvas API Documentation: https://canvas.instructure.com/doc/api/all_resources.html#method.courses.users
def get_users_in_course(course_id):
    url = f"{CANVAS_API_URL}/api/v1/courses/{course_id}/users"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    # Optional request params
    params = {
        "sort": "email",
        "enrollment_state": "active"
    }

    users = []
    while url:
        try: 
            # Make API request
            response = requests.get(url, headers=headers, params=params)

            # Checks if response was successful
            response.raise_for_status()

            # Process response into json format
            data = response.json()
            users.extend(data)
            return users
        except requests.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {response.status_code} {response.reason}")
            break
        except requests.RequestException as req_err:
            print(f"An error occurred: {req_err}")
            break
        except Exception as err:
            print(f"Something went wrong: {err}")
            break
    return users

# Retrieve users 
users = get_users_in_course(COURSE_ID)

if users:
    print("Users in the course:")
    for user in users:
        print(f"Name: {user['name']}, Email: {user['email']}")
else:
    print("No users found or unable to fetch users.")

