# Setting up python 
1. Create Env. `conda env create -f pyqt-env.yml` 
2. Activate `conda activate pyqt-env` 
3. Update packages `conda env update -f pyqt-env.yml --prune`

# Setting up Canvas access token 
1. Login into Canvas and navigate to the Settings Tab under your Account
2. Scroll down until you find the Approved Integrations subsection
3. Create an access token by clicking New Access Token button, specifying the purpose and expiration date.
4. Copy the new access token and save it somewhere on your computer.

# Running *canvas_data.py* script
1. Create an `.env` file and store your canvas access token as `API_TOKEN`
2. Run python script `python canvas_data.py`


# Running google script
0. Setup google project with API support, allow users to test ap!
1. Download credentials
2. The credentials are not pushed to git, it should be a `./client_secrets.json` 
3. run the python script `python ./GoogleServices/GoogleServices.py/` or use the `./google_forms.ipynb`
