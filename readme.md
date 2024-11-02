# Running Python Script
Before running the script, please complete the **Python environment setup** to ensure all necessary libraries are installed.
## Prerequisites
1. **Complete the [Setting up Python](#setting-up-python) section** for required installations.
2. Ensure the Canvas access token is configured (see [Setting up Canvas access token](#setting-up-canvas-access-token)).
## Steps:
1. Navigate to the project directory and Run `python GradingAutomationUI.py`
2. Enter the canvas class id, your canvas access token, and the presentation module title.
   
   For this demo, the class id is `15319` and the presentation module title is `Fall 2024 - Presentation`
   
    <img width="1186" alt="Screenshot 2024-11-01 at 4 29 14 PM" src="https://github.com/user-attachments/assets/d814e957-45bf-4f06-8d14-9b09df544b76">

3. Locate the path for this git repository and Click on "Verify Selected Projects".

   A sample output would look like this:

   <img width="1153" alt="Screenshot 2024-11-01 at 4 38 02 PM" src="https://github.com/user-attachments/assets/3068a5fe-341c-4c09-9b07-00bb542dbddb">

4. Navigate to "Page Management" and Select rows to create pages from the group folders in the repository.

   A sample output of creating pages for three test projects would look like this:

   <img width="1172" alt="Screenshot 2024-11-01 at 4 44 15 PM" src="https://github.com/user-attachments/assets/93837ea9-9423-408c-b500-f397830db12f">


5. In the "Forms and Quizzes Tab", you can select created pages to add feedback forms and quizzes.

   Sample output for adding feedback form and quiz for the "SampleTeam_f4" page:

   <img width="1178" alt="Screenshot 2024-11-01 at 4 46 17 PM" src="https://github.com/user-attachments/assets/0f2e9b56-cc19-4d88-97d9-e35c7462b33f">

6. Clicking on the "Close and Grade" button would remove the feedback form on the team page, update the page with a grade distribution from the feedback forms, and post the grade for the team members.

    Sample page output on Canvas after retrieving grade distribution from feedback forms:

   <img width="967" alt="Screenshot 2024-11-01 at 5 00 23 PM" src="https://github.com/user-attachments/assets/57b3ded5-5b4e-46fa-af93-ca84b56ad265">

---
## Setting up python 

### Using Conda Environment
1. Create Env. 
    ```bash 
    conda env create -f pyqt-env.yml
    ```
2. Activate 
    ```sh 
    conda activate pyqt-env
    ```
3. Update packages 
    ```bash 
    conda env update -f pyqt-env.yml --prune
    ```

### Using Python Requirements File
1. Create a virtual environment:
    ```sh
    python -m venv venv
    ```
2. Activate the virtual environment:
      - On Windows:
        ```bash
        venv\Scripts\activate
        ```
      - On macOS and Linux:
        ```bash 
        source venv/bin/activate
        ```
1. Install packages from requirements.txt:
    ```bash 
    pip install -r requirements.txt
    ```
2. To update packages, modify the requirements.txt file and run:
    ```bash
    pip install --upgrade -r requirements.txt
    ```

--- 
## Setting up Canvas access token 
1. Login into Canvas and Navigate to Account Settings
   
![Screenshot 2024-11-01 155422](https://github.com/user-attachments/assets/5ff675c1-6937-40d7-a479-8098c759c743)

2. Scroll down until you find the <u>Approved Integrations subsection</u> and Create an access token by clicking New Access Token button

![Screenshot 2024-11-01 160318](https://github.com/user-attachments/assets/bae4a0f4-0ab8-43d1-abb9-d87a9aca6c51)

3. Specify the purpose and expiration date, create the new access token, save it on your computer.

![Screenshot 2024-11-01 160721](https://github.com/user-attachments/assets/fa7eea3f-9385-4379-8f06-6967d389251f)

--- 
## Running google script
0. Setup google project with API support, allow users to test ap!
1. Download credentials
2. The credentials are not pushed to git, it should be a `./client_secrets.json` 
3. Run the python script `python ./GoogleServices/GoogleServices.py/` or use the `./google_forms.ipynb`


##  Data visualization of grades 
1. Set up python based on above instructions - [Setting up Python](#setting-up-python)
2. Place `S24-574-all-responses.xlsx` in this same directory 
3. Open `./removing_outliers.ipynb`  
4. Select the python environment `pyqt-env`  or `venv`  
5. Click on run all
