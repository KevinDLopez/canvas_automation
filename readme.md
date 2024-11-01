# Running Python Script
Before running the script, please complete the **Python environment setup** to ensure all necessary libraries are installed.
## Prerequisites
1. **Complete the [Setting up Python](#setting-up-python) section** for required installations.
2. Ensure the Canvas access token is configured (see [Setting up Canvas access token](#setting-up-canvas-access-token)).
## Steps:

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
