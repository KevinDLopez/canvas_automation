# Setting up python 

## Using Conda Environment
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

## Using Python Requirements File
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
   
# Setting up Canvas access token 
1. Login into Canvas and navigate to the Settings Tab under your Account
2. Scroll down until you find the Approved Integrations subsection
3. Create an access token by clicking New Access Token button, specifying the purpose and expiration date.
4. Copy the new access token and save it somewhere on your computer.

# Running *canvas_data.py* script
1. Create an `.env` file and store your canvas access token as `API_TOKEN`
2. Run python script `python test_canvas_service.py`


# Running google script
0. Setup google project with API support, allow users to test ap!
1. Download credentials
2. The credentials are not pushed to git, it should be a `./client_secrets.json` 
3. run the python script `python ./GoogleServices/GoogleServices.py/` or use the `./google_forms.ipynb`


# For running `removing_outliers.ipynb` - data visualization of grades 
1. Set up python based on above instructions - [Setting up Python](#setting-up-python)
2. Place `S24-574-all-responses.xlsx` in this same directory 
3. Open `./removing_outliers.ipynb`  
4. Select the python environment `pyqt-env`  or `venv`  
5. click on run all